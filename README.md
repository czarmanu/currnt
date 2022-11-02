#CURRNT
The Combined Utilities for River Routing Nested Together (CURRNT) is designed to
simplify the execution of the Routing Application for Parallel computatIon of 
Discharge (RAPID) and the Reproducible Routing Rituals (RRR) on Amazon Web
Services (AWS).

## Local execution
Download CURRNT:

```
git clone https://github.com/c-h-david/currnt
```

Enter the CURRNT directory:

```
cd currnt/
```

Create Docker image

```
docker build -t chdavid/currnt:app0 -f Dockerfile_app0 .
```

Execute Docker image as a Docker container. The `--rm` option deletes the
container after execution. The `-p 9000:8080` option maps Transmission Control
Protocol (TCP) ports. In this case, the `8080` port in the Docker container is
mapped to the `9000` port in the Docker host.

```
docker run --rm -p 9000:8080 chdavid/currnt:app0
```

Try it out:

```
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"LSM":"VIC"}'
```
