"""Resources management server module under Rotest framework.

The server accepts new clients and creates a worker (that runs in an
independent thread) for each of them.

The worker's job is to accept messages from the corresponding client, decode
them and put them in the Messages queue.

The server's main thread pops messages from the queue and handles them.
"""
