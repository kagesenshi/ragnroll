from .. import settings
import fastapi
import neo4j

def connect(request: fastapi.Request) -> neo4j.AsyncDriver:
    params = dict(
        uri=settings.NEO4J_URI,
        database=settings.NEO4J_DATABASE,
    )

    if settings.NEO4J_USE_SSL:
        params['encrypted'] = True
        if settings.NEO4J_SSL_CA_CERT:
            params['trusted_certificates'] = neo4j.TrustCustomCAs(settings.NEO4J_SSL_CA_CERT)

    auth_header = request.headers.get('Authorization', default=None)
    if settings.NEO4J_USE_BEARER_TOKEN and auth_header and auth_header.lower().startswith('bearer'):
        params['auth'] = neo4j.bearer_auth(auth_header.split(' ')[1])
    else:
        if settings.NEO4J_USERNAME and settings.NEO4J_PASSWORD:
            params['auth'] = (settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        else:
            raise fastapi.HTTPException(status_code=401, detail='Neither database login configured nor authorization header provided')

    return neo4j.AsyncGraphDatabase.driver(**params)

