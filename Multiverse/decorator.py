"""
decorator.py

Provides the @universe decorator to run functions in specified virtual
environments.
"""

import socket
import cloudpickle
import sys
from .virtual_env_manager import VirtualEnvManager


class WorkerClient:
    """
    Client that communicates with the worker process to execute functions.
    """

    def __init__(self, env_name, port):
        self.env_name = env_name
        self.host = '127.0.0.1'
        self.port = port

    def execute(self, func, *args, **kwargs):
        """
        Executes the function in the worker environment.
        """
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            data = cloudpickle.dumps((func, args, kwargs)) + b'END'
            sock.sendall(data)
            response_data = b''
            while True:
                packet = sock.recv(4096)
                if not packet:
                    break
                response_data += packet
            response = cloudpickle.loads(response_data)
            if 'exception' in response:
                print(response.get('stderr', ''), file=sys.stderr)
                raise response['exception']
            else:
                print(response.get('stdout', ''), end='')
                return response['result']
        except Exception as e:
            error_message = f"Error executing function in environment " \
                            f"'{self.env_name}': {e}"
            print(error_message, file=sys.stderr)
            raise
        finally:
            if sock:
                sock.close()


def universe(env_name=None, existing_env_path=None):
    """
    Decorator to run functions in a specified virtual environment.
    """
    if env_name is None and existing_env_path is None:
        raise ValueError("Must specify either 'env_name' or "
                         "'existing_env_path'.")

    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = VirtualEnvManager.get_instance()
            if existing_env_path:
                # Use existing environment path directly
                env_path = existing_env_path
                env_key = f"external_{env_path}"
                if env_key not in manager.workers:
                    manager.start_worker(env_key, env_path)
                port = manager.workers[env_key]['port']
                client = WorkerClient(env_key, port)
            else:
                if env_name not in manager.workers:
                    raise ValueError(f"Environment '{env_name}' is not "
                                     f"available.")
                port = manager.workers[env_name]['port']
                client = WorkerClient(env_name, port)
            return client.execute(func, *args, **kwargs)
        return wrapper
    return decorator
