# CURRNT

[![License (3-Clause BSD)][BDG_BSD3]][URL_LICENS]

[![Docker Images][BDG_DOC]][TAG_DOC]

[![Docker Images][BDG_ZEN]][URL_ZEN]

[![GitHub CI Status][BDG_CI]][URL_CI]

[![GitHub CD Status][BDG_CD]][URL_CD]

The Combined Utilities for River Routing Nested Together (CURRNT) is designed
to simplify the execution of the Routing Application for Parallel computatIon
of Discharge (RAPID) and the Reproducible Routing Rituals (RRR) on Amazon Web
Services (AWS).

## Local execution

Download CURRNT:

```bash
git clone https://github.com/c-h-david/currnt
```

Enter the CURRNT directory:

```bash
cd currnt/
```

Create Docker image:

```bash
docker build -t chdavid/currnt:scaffold0-latest -f Dockerfile_scaffold0 .
```

Execute Docker image as a Docker container:

```bash
docker run --rm -p 9000:8080 chdavid/currnt:scaffold0-latest
docker run -e EARTHDATA_USERNAME="yourEarthDataUserName" \
           -e EARTHDATA_PASSWORD="yourEarthDataPassword" \
           --rm -p 9000:8080 chdavid/currnt:scaffold3-latest
docker run -e EARTHDATA_USERNAME="yourEarthDataUserName" \
           -e EARTHDATA_PASSWORD="yourEarthDataPassword" \
           -e AWS_ACCESS_KEY_ID="yourKeyID" \
           -e AWS_SECRET_ACCESS_KEY="yourSecretAccessKey" \
           --rm -p 9000:8080 chdavid/currnt:scaffold4-latest
```

> The `--rm` option deletes the container after execution. The `-p 9000:8080`
> option maps Transmission Control Protocol (TCP) ports. In this case, the
> `8080` port in the Docker container is mapped to the `9000` port in the
> Docker host. Also, if one of your environmental variables has a special
> character,> consider using the `\` escape character before the special
> character.

Try it out:

```bash
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
     --data-raw '{"basin_id":"74", "lsm_mod":"VIC",
                  "s3_name":"currnt-data", "yyyy_mm":"2000-01"}'
```

[BDG_BSD3]: https://img.shields.io/badge/license-BSD%203--Clause-yellow.svg
[BDG_DOC]: https://img.shields.io/badge/docker-images-blue?logo=docker
[BDG_ZEN]: https://zenodo.org/badge/DOI/10.5281/zenodo.14206902.svg
[URL_LICENS]: https://github.com/c-h-david/currnt/blob/main/LICENSE
[TAG_DOC]: https://hub.docker.com/r/chdavid/currnt/tags
[URL_ZEN]: https://doi.org/10.5281/zenodo.14206902

<!-- pyml disable-num-lines 20 line-length-->
[BDG_CI]: https://github.com/czarmanu/currnt/actions/workflows/github_actions_CI.yml/badge.svg
[BDG_CD]: https://github.com/c-h-david/currnt/actions/workflows/github_actions_CD.yml/badge.svg
[URL_CI]: https://github.com/czarmanu/currnt/actions/workflows/github_actions_CI.yml
[URL_CD]: https://github.com/c-h-david/currnt/actions/workflows/github_actions_CD.yml
