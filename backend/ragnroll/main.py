import argparse
import sys
import fastapi
import uvicorn
import functools
import asyncio
import neo4j
from .db import connect

serve = functools.partial(uvicorn.run, 'ragnroll.app:app')

async def _initdb(txn: neo4j.AsyncTransaction):
    query = '''
        CREATE VECTOR INDEX ragquestion_embedding IF NOT EXISTS
            FOR (n:_RAGQuestion)
            ON (n.embedding)
            OPTIONS { indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
                }
            }
    '''   
    await txn.run(query)

async def initdb():
    driver = connect(None)
    session: neo4j.AsyncSession = driver.session()
    async with session:
        await session.execute_write(_initdb)
    print('InitDB Completed')

async def get_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    serve_parser = subparsers.add_parser('serve', help='Serve the application')
    serve_parser.add_argument('-l', '--host', default='127.0.0.1')
    serve_parser.add_argument('-p', '--port', type=int, default=5000)
    serve_parser.add_argument('-r', '--reload', action='store_true', default=False)

    init_parser = subparsers.add_parser('initdb', help='Initialize DB')
    return parser

def run(args=sys.argv[1:]):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(arun(args))

async def arun(args=sys.argv[1:]):
    commands = {
        'serve': serve,
        'initdb': initdb
    }

    parser = await get_parser()
    p_args = parser.parse_args(args=args)
    if getattr(p_args, 'command', None) is None: 
        parser.print_help()
        sys.exit(1)

    f = commands[p_args.command]
    kwargs = dict(p_args._get_kwargs())
    args = p_args._get_args()
    del kwargs['command']
    out = await f(*args, **kwargs)
    if out is None:
        sys.exit(0)
    sys.exit(out)

if __name__ == '__main__':
    run()
