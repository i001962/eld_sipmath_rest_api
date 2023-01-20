from flask import Flask, jsonify, request
from volatility import compute_volatility
from scheduler import run_jobs
from threading import Thread
import logging
import os

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# scheduler job thread
scheduler_thread = Thread(target=run_jobs, daemon=True)
scheduler_thread.start()


@app.route('/')
def index():
    result = {
        "message": "Volatility API Endpoint",
        "method": "GET",
        "usage_example": "volatility/?tickers=SOLACE,ETH&window=365&terms=3"
    }
    return jsonify(result)


@app.route('/volatility/', methods=['GET'])
def volatility():
    if request.method == "GET":
        try:
            logging.info("=" * 100)
            protocols = request.args.get('protocols')
            window = int(request.args.get('window'))
            terms = int(request.args.get('terms'))
            response, token_map = compute_volatility(protocols, window, terms)
            logging.info("=" * 100)

            if not response:
                raise Exception("An internal error occurred while calculating the volatility. Please refer to the "
                                "server logs.")

            response["status_code"] = 200
            response["message"] = "Successful"
            response["error"] = False
            response["error_message"] = None
            response["token_map"] = token_map
            return jsonify(response)
        except Exception as e:
            logging.error("Something went wrong. Error: %s" % e)
            response = {
                "status_code": 500,
                "message": "Not Successful",
                "error": True,
                "error_message": "%s" % e,
                "token_map": []
            }
            return jsonify(response)


if __name__ == "__main__":
    logging.info("Volatility Metadata Bucket Name: {}".format(os.environ.get('VOLATILITY_METADATA_BUCKET_NAME')))
    logging.info("Volatility Cache Bucket Name: {}".format(os.environ.get('VOLATILITY_CACHE_BUCKET_NAME')))
    logging.info("Volatility Key: {}".format(os.environ.get('VOLATILITY_KEY')))
    logging.info("Volatility Metadata Key: {}".format(os.environ.get('VOLATILITY_METADATA_KEY')))
    app.run(debug=True, host="0.0.0.0", port=8089)
