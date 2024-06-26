import os
import platform
import requests
import sys
import subprocess
import zipfile

from jinja2 import Environment, FileSystemLoader
from OpenSSL import crypto
from threading import Thread

from application.common import logger, constants
from application.common.decorators import timeit
from application.common.exceptions import NginxException
from application.common.toolbox import _get_proc_by_name, _get_application_path

from operator_client import Operator

# References:
# https://nachtimwald.com/2019/11/14/python-self-signed-cert-gen/


class NginxManager:
    def __init__(self, client: Operator) -> None:
        self._exe_name = None
        self._exe_path = None
        self._exe_full_path = None
        self._exe_thread = None

        self._client: Operator = client

        self._platform = platform.system()

    def is_running(self) -> bool:
        return True if _get_proc_by_name(self._exe_name) else False

    def nginx_status(self):
        process_info = None
        process = _get_proc_by_name(self._exe_name)

        if process:
            process_info = process.as_dict()
            pass

        return process_info

    def get_public_key_content(self) -> str:
        if os.path.exists(constants.SSL_CERT_FILE):
            with open(constants.SSL_CERT_FILE, "r") as f:
                return f.read()
        else:
            return None

    def key_pair_exists(self) -> bool:
        key_file_exists = os.path.exists(constants.SSL_KEY_FILE)
        cert_file_exists = os.path.exists(constants.SSL_CERT_FILE)
        return key_file_exists and cert_file_exists

    def remove_ssl_key_pair(self) -> None:
        if os.path.exists(constants.SSL_KEY_FILE):
            os.remove(constants.SSL_KEY_FILE)
        if os.path.exists(constants.SSL_CERT_FILE):
            os.remove(constants.SSL_CERT_FILE)

    def generate_ssl_certificate(self, initialize=None) -> None:
        if initialize:
            nginx_proxy_hostname = initialize[constants.SETTING_NGINX_PROXY_HOSTNAME]
        else:
            nginx_proxy_hostname = self._client.app.get_setting_by_name(
                constants.SETTING_NGINX_PROXY_HOSTNAME
            )

        validityEndInSeconds = 365 * 24 * 60 * 60  # One Year

        if not os.path.exists(constants.SSL_FOLDER):
            os.makedirs(constants.SSL_FOLDER, exist_ok=True)

        # create a key pair
        pub_key = crypto.PKey()
        pub_key.generate_key(crypto.TYPE_RSA, 4096)
        # create a self-signed cert

        cert = crypto.X509()

        # This is so the client requesting the set hostname will match to subject.
        cert.get_subject().CN = nginx_proxy_hostname
        cert.set_serial_number(0)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(validityEndInSeconds)
        cert.set_issuer(cert.get_subject())

        # Really setting to version 3 based on index starting at 0.
        cert.set_version(2)

        # The SAN must have some extra info added if the hostname is an IP address, so need to
        # check and act accoringly.
        san_dns_list = [
            "DNS:localhost",
            "DNS:*.localhost",
        ]
        if self._is_string_ip_address(nginx_proxy_hostname):
            san_dns_list.append(f"IP:{nginx_proxy_hostname}")
        else:
            san_dns_list.append(f"DNS:{nginx_proxy_hostname}")
            san_dns_list.append(f"DNS:*.{nginx_proxy_hostname}")

        # If Subject altnerative name is not set to the hostname desired, the python requests
        # package will throw an sslError based on hostname mismatch.
        # Also - Add localhost so testing as localhost works.
        cert.add_extensions(
            [
                crypto.X509Extension(
                    b"subjectAltName",
                    False,
                    ",".join(san_dns_list).encode(),
                ),
                crypto.X509Extension(b"basicConstraints", True, b"CA:false"),
            ]
        )

        cert.set_pubkey(pub_key)

        cert.sign(pub_key, "sha512")

        with open(constants.SSL_CERT_FILE, "wt") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))
        with open(constants.SSL_KEY_FILE, "wt") as f:
            f.write(
                crypto.dump_privatekey(crypto.FILETYPE_PEM, pub_key).decode("utf-8")
            )

    def startup(self, initialize=None) -> None:
        if self.is_running():
            self._stop_nginx()
        self._spawn_nginx(initialize=initialize)

    def shutdown(self) -> None:
        if self._stop_nginx():
            self._exe_thread.join()

    def _is_string_ip_address(self, s) -> bool:
        a = s.split(".")
        if len(a) != 4:
            return False
        for x in a:
            if not x.isdigit():
                return False
            i = int(x)
            if i < 0 or i > 255:
                return False
        return True

    @staticmethod
    def _print_command(list_list: list):
        output = ""
        for item in list_list:
            output += item + " "
        logger.info(output)

    def _spawn_exe(self, command: [], cwd: str) -> None:
        result = subprocess.run(
            command,
            creationflags=subprocess.DETACHED_PROCESS,  # Use this on windows-specifically.
            close_fds=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
        )

        return result

    def _launch_nginx(self, input_args={}, use_equals=False, working_dir=None) -> None:
        """
        This function is meant to launch an nginx server / reverse proxy.

        Start a generic executable server with the input arguments provided, if any.

        Args:
            input_args (dict): Dictionary of key value pairs to use
            as inputs arguments.
            use_equals (bool): If true, input arguments are appended with key=value
        """
        if not os.path.exists(self._exe_full_path):
            raise NginxException(
                f"The executable file does not exist: {self._exe_full_path}"
            )

        exe_command = [self._exe_full_path]

        format_string = '{key}="{value}"' if use_equals else "{key} {value}"

        if len(input_args.keys()) > 0:
            for arg in input_args:
                exe_command.append(format_string.format(key=arg, value=input_args[arg]))

        # Get folder
        execution_folder = os.path.dirname(self._exe_full_path)

        if working_dir:
            execution_folder = working_dir

        self._print_command(exe_command)

        self._exe_thread = Thread(
            target=lambda: self._spawn_exe(exe_command, execution_folder)
        )

        self._exe_thread.daemon = True
        self._exe_thread.start()

    def _stop_nginx(self) -> bool:
        process = None
        is_process_stopped = False

        process = _get_proc_by_name(self._exe_name)

        while process:
            process = _get_proc_by_name(self._exe_name)

            if process:
                process.terminate()
                process.wait()
                is_process_stopped = True

        return is_process_stopped

    @timeit
    def _download_nginx_server(self):
        file_name = constants.NGINX_STABLE_RELEASE_WIN.split("/")[-1]

        # This is where nginx down be downloaded and run from.
        nginx_folder_path = os.path.join(constants.DEFAULT_INSTALL_PATH, "nginx")
        nginx_save_path = os.path.join(nginx_folder_path, file_name)

        if not os.path.exists(nginx_folder_path):
            os.makedirs(nginx_folder_path, exist_ok=True)

            response = requests.get(constants.NGINX_STABLE_RELEASE_WIN, stream=True)
            with open(nginx_save_path, "wb") as fd:
                for chunk in response.iter_content(chunk_size=128):
                    fd.write(chunk)

            with zipfile.ZipFile(nginx_save_path, "r") as zip_ref:
                zip_ref.extractall(nginx_folder_path)

    @timeit
    def _spawn_nginx(self, initialize=None):
        self._download_nginx_server()

        if initialize:
            nginx_proxy_hostname = initialize[constants.SETTING_NGINX_PROXY_HOSTNAME]
            nginx_proxy_port = initialize[constants.SETTING_NGINX_PROXY_PORT]
        else:
            nginx_proxy_hostname = self._client.app.get_setting_by_name(
                constants.SETTING_NGINX_PROXY_HOSTNAME
            )

            nginx_proxy_port = self._client.app.get_setting_by_name(
                constants.SETTING_NGINX_PROXY_PORT
            )

        nginx_folder = os.path.join(
            constants.DEFAULT_INSTALL_PATH, "nginx", constants.NGINX_VERSION
        )
        nginx_conf_folder = os.path.join(
            constants.DEFAULT_INSTALL_PATH, "nginx", constants.NGINX_VERSION, "conf"
        )
        nginx_conf_full_path = os.path.join(nginx_conf_folder, "nginx.conf")

        nginx_config_conf_folder = os.path.join(
            _get_application_path(), "config", "nginx"
        )

        pub_key_file = constants.SSL_CERT_FILE.replace("\\", "/")
        private_key_file = constants.SSL_KEY_FILE.replace("\\", "/")

        # Create a formatted nginx conf file.
        env = Environment(loader=FileSystemLoader(nginx_config_conf_folder))
        template = env.get_template("nginx.conf.j2")
        output_from_parsed_template = template.render(
            NGINX_PROXY_HOSTNAME=nginx_proxy_hostname,
            NGINX_PROXY_PORT=nginx_proxy_port,
            NGINX_PUBLIC_KEY=pub_key_file,
            NGINX_PRIVATE_KEY=private_key_file,
        )

        if os.path.exists(nginx_conf_full_path):
            os.remove(nginx_conf_full_path)

        with open(nginx_conf_full_path, "w") as myfile:
            myfile.write(output_from_parsed_template)

        self._exe_name = "nginx.exe"
        self._exe_path = nginx_folder
        self._exe_full_path = os.path.join(self._exe_path, self._exe_name)

        # If already running, kill the nginx server.
        if self._stop_nginx():
            logger.info("NGINX: Stopped existing instance before startup...")

        try:
            self._launch_nginx(working_dir=nginx_folder)
        except Exception as error:
            message = "Unable to launch executable."
            logger.error(message)
            logger.critical(error)
            sys.exit(1)
