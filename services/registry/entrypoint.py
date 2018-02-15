""" Service entrypoint for docker compose which also act as a bootstrap for service.
"""
from ._impl import service


if __name__ == '__main__':
    container = service.create_container()
    container.start()
    container.wait()
