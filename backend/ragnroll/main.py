import argparse
import sys
import fastapi
import uvicorn
import functools

serve = functools.partial(uvicorn.run, 'ragnroll.app:app')

def get_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    serve_parser = subparsers.add_parser('serve', help='Serve the application')
    serve_parser.add_argument('-l', '--host', default='127.0.0.1')
    serve_parser.add_argument('-p', '--port', type=int, default=5000)
    serve_parser.add_argument('-r', '--reload', action='store_true', default=False)
    return parser

def run(args=sys.argv[1:]):

    commands = {
        'serve': serve
    }

    parser = get_parser()
    p_args = parser.parse_args(args=args)
    if getattr(p_args, 'command', None) is None: 
        parser.print_help()
        sys.exit(1)

    f = commands[p_args.command]
    kwargs = dict(p_args._get_kwargs())
    args = p_args._get_args()
    del kwargs['command']
    out = f(*args, **kwargs)
    if out is None:
        sys.exit(0)
    sys.exit(out)

if __name__ == '__main__':
    run()
