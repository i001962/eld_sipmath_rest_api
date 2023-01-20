import json
from collections import deque
from datetime import datetime, timezone
import schedule
from urllib.parse import urlparse, parse_qs
from volatility import compute_volatility
from s3 import *
import logging


def get_job_definitions():
    metadata = json.loads(s3_get_volatility_metadata())
    urls = metadata['urls']
    jobs = []

    for url in urls:
        try:
            timestamp = url['timestamp']
            url_query_params = parse_qs(urlparse(url['url']).query)
            protocols = url_query_params['protocols'][0]
            window = int(url_query_params['window'][0])
            terms = int(url_query_params['terms'][0])
            diff = datetime.utcnow() - datetime.utcfromtimestamp(timestamp)

            if int(diff.days) <= 0:
                continue

            jobs.append(
                {
                    'url': url['url'],
                    'timestamp': timestamp,
                    'protocols': protocols,
                    'window': window,
                    'terms': terms
                }
            )
        except Exception as e:
            msg = "get_job_definitions(): Error occurred while getting volatility job definitions. Url: {}\nError: {}".format(url, e)
            logging.error(msg)
    return jobs


def compute_volatility_jobs():
    metadata = {"urls": []}
    job_queue = deque(get_job_definitions())

    logging.info("compute_volatility_job(): Job Length: {}".format(len(job_queue)))

    while True:
        if len(job_queue) == 0:
            logging.info("compute_volatility_job(): There is no job.")
            break

        job = job_queue.popleft()
        try:

            result, token_map = compute_volatility(job['protocols'], job['window'], job['terms'])
            result["token_map"] = token_map

            if len(token_map) > 0:
                # update cache result
                s3_put_volatility(json.dumps(result))
                metadata["urls"].append({"url": job['url'], "timestamp": int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp())})

            logging.info("compute_volatility_job(): Job finished for url: {}".format(job['url']))
            logging.info("compute_volatility_job(): Remaining job count: {}".format(len(job_queue)))
            time.sleep(60)
        except Exception as e:
            msg = "compute_volatility_job(): Error occurred while calculating volatility job. Job: {}\nError: {}".format(job, e)
            logging.error(msg)
            logging.info("compute_volatility_job(): Adding job to queue. Url: {}".format(job['url']))
            logging.info("compute_volatility_job(): Job Length: {}".format(len(job_queue)))
            job_queue.append(job)
            time.sleep(60)

    try:
        if len(metadata['urls']) > 0:
            s3_update_metadata(json.dumps(metadata))
    except Exception as e:
        msg = "compute_volatility_job(): Error occurred while updating metadata information for volatility. Error: {}".format(e)
        logging.error(msg)


def run_jobs():
    logging.info("run_jobs(): Scheduler has been started")
    schedule.every().day.at("00:00").do(compute_volatility_jobs)
    #schedule.every(1).minutes.do(compute_volatility_jobs)
    while True:
        schedule.run_pending()
        time.sleep(1)
