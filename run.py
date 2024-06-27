import logging

from app import create_app
from flask import render_template, request
import flask
from app.utils.flights import get_flights
from app.utils.whatsapp_utils import (get_templated_message_input, send_message)

app = create_app()

@app.route("/catalog")
def catalog():
    flights = get_flights()
    return render_template('catalog.html', title='Demo', flights=flights)


@app.route("/buy-ticket", methods=['POST'])
async def buy_ticket():
  flight_id = int(request.form.get("id"))
  flights = get_flights()
  flight = next(filter(lambda f: f['flight_id'] == flight_id, flights), None)
  data = get_templated_message_input(app.config['RECIPIENT_WAID'], flight)

  await send_message(data)

  return flask.redirect(flask.url_for('catalog'))


@app.route('/welcome', methods=['POST'])
async def welcome():
  return flask.redirect(flask.url_for('catalog'))


if __name__ == "__main__":
    logging.info("Flask app started")
    app.run(host="0.0.0.0", port=8000)
