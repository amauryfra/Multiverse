"""
virtual_env_manager.py

Manages virtual environments and worker processes based on a YAML
configuration.
"""

import yaml
import subprocess
import os
import threading
import socket
import sys
import atexit
import tempfile


class VirtualEnvManager:
    """
    Singleton class that manages virtual environments and worker processes.
    """

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, config_file=None):
        """
        Returns the singleton instance of VirtualEnvManager.
        """
        with cls._lock:
            if cls._instance is None:
                if config_file is None:
                    raise ValueError("First initialization requires a "
                                     "config_file")
                cls._instance = cls(config_file)
            return cls._instance

    def __init__(self, config_file):
        if VirtualEnvManager._instance is not None:
            raise Exception("This class is a singleton")
        self.workers = {}
        self.lock = threading.Lock()
        self.used_ports = set()
        self.env_paths = {}
        self.base_dir = os.path.abspath('virtualenvs')
        os.makedirs(self.base_dir, exist_ok=True)

        with open(config_file) as f:
            config = yaml.safe_load(f)

        for env_name, env_config in config.get('environments', {}).items():
            existing_env_path = env_config.get('existing_env_path')
            if existing_env_path:
                env_path = os.path.abspath(existing_env_path)
            else:
                env_path = os.path.join(self.base_dir, env_name)
                self.create_virtualenv(env_path, env_config)
            self.env_paths[env_name] = env_path
            self.start_worker(env_name, env_path)

        atexit.register(self.stop_workers)

    @staticmethod
    def create_virtualenv(env_path, env_config):
        """
        Creates a virtual environment and installs specified packages.
        """
        python_version = env_config.get('python_version', 'python3')
        if not os.path.exists(env_path):
            subprocess.check_call([python_version, '-m', 'venv', env_path])
        # Ensure cloudpickle is installed
        pip_path = os.path.join(env_path, 'bin', 'pip')
        subprocess.check_call([pip_path, 'install', '--upgrade', 'pip'])
        subprocess.check_call([pip_path, 'install', 'cloudpickle'])
        # Install packages from requirements file
        requirements_file = env_config.get('requirements_file')
        if requirements_file:
            subprocess.check_call(
                [pip_path, 'install', '-r', requirements_file]
            )
        # Install packages specified in 'packages' list
        packages = env_config.get('packages', [])
        if packages:
            subprocess.check_call([pip_path, 'install'] + packages)

    def find_free_port(self):
        """
        Finds a free port for the worker to listen on.
        """
        with self.lock:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', 0))
            port = sock.getsockname()[1]
            sock.close()
            while port in self.used_ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('', 0))
                port = sock.getsockname()[1]
                sock.close()
            self.used_ports.add(port)
            return port

    def start_worker(self, env_name, env_path):
        """
        Starts a worker process for the given environment.
        """
        python_path = os.path.join(env_path, 'bin', 'python')
        script_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'worker.py')
        )
        port = self.find_free_port()
        # Start the worker process
        cmd = [python_path, script_path,
               '--env-name', env_name,
               '--port', str(port)]
        proc = subprocess.Popen(cmd)
        self.workers[env_name] = {'process': proc, 'port': port}

    def stop_workers(self):
        """
        Stops all worker processes.
        """
        for env_name, info in self.workers.items():
            proc = info['process']
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        self.workers.clear()
        self.used_ports.clear()

    def __del__(self):
        self.stop_workers()
