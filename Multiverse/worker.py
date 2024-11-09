"""
worker.py

Worker process that listens for function execution requests and runs them.
"""

import argparse
import socket
import cloudpickle
import sys
import threading
import io
import traceback


def handle_client(conn):
    """
    Handles incoming client connections and executes functions.
    """
    try:
        data = b''
        while True:
            packet = conn.recv(4096)
            if not packet:
                break
            data += packet
            if data.endswith(b'END'):
                break
        data = data[:-3]  # Remove 'END'
        func, args, kwargs = cloudpickle.loads(data)
        stdout = io.StringIO()
        stderr = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = stdout
        sys.stderr = stderr
        try:
            result = func(*args, **kwargs)
            output = stdout.getvalue()
            error_output = stderr.getvalue()
            response = cloudpickle.dumps({
                'result': result,
                'stdout': output,
                'stderr': error_output
            })
        except Exception as e:
            error_output = stderr.getvalue() + '\n' + traceback.format_exc()
            response = cloudpickle.dumps({
                'exception': e,
                'stderr': error_output
            })
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            stdout.close()
            stderr.close()
        conn.sendall(response)
    except Exception as e:
        error_response = cloudpickle.dumps({
            'exception': e,
            'stderr': traceback.format_exc()
        })
        conn.sendall(error_response)
    finally:
        conn.close()


def main():
    """
    Main function to start the worker server.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--env-name', required=True)
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()

    env_name = args.env_name
    host = '127.0.0.1'
    port = args.port

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((host, port))
    server_sock.listen(5)
    print(f"Worker for {env_name} listening on {host}:{port}", file=sys.stderr)
    while True:
        try:
            conn, addr = server_sock.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Server error: {e}", file=sys.stderr)
    server_sock.close()


if __name__ == '__main__':
    main()
