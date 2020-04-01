#!/usr/bin/env python

import argparse
import logging
import requests
from datetime import datetime
from server_utils import assert_http_uri, assert_mysql_db_uri, assert_email
from sqlalchemy.engine.url import make_url
import re

class HandoverClient(object):

    """
    Client for submitting databases for handover
    """

    handovers = '{}handovers/'
    handover_token = '{}handovers/{}'

    def __init__(self, uri):
        assert_http_uri(uri)
        self.uri = uri

    def submit_handover(self, spec):
        """
        Arguments:
          spec : dict containing keys `src_uri`, `comment` and `contact`
        """
        assert_mysql_db_uri(spec['src_uri'])
        assert_email(spec['contact'])
        logging.info("Submitting {} for handover".format(spec['src_uri']))
        logging.debug(spec)
        r = requests.post(self.handovers.format(self.uri), json=spec)
        r.raise_for_status()
        return r.json()

    def list_handovers(self):
        """
        Retrieve full list of handover databases
        """
        logging.info("Listing")
        r = requests.get(self.handovers.format(self.uri))
        r.raise_for_status()
        return r.json()

    def print_handover_detail(self, handover):
        """
        Print out details of a handover
        Arguments:
          handover : Handover dict
        """
        report_time = datetime.strptime(handover['report_time'],"%Y-%m-%dT%H:%M:%S.%f")
        if 'current_message' in handover:
            logging.info("Handover %s (%s) submitted by (%s) - %s on %s" % (handover['handover_token'], handover['src_uri'], handover['contact'], handover['current_message'],report_time.strftime('%d-%m-%Y %H:%M')))
        elif 'message' in handover:
            logging.info("Handover %s (%s) submitted by (%s) - %s on %s" % (handover['handover_token'], handover['src_uri'], handover['contact'], handover['message'], report_time.strftime('%d-%m-%Y %H:%M')))

    def retrieve_handover(self, handover_token):
        """
        Retrieve a handover using an handover_token
        Arguments:
          handover_token: handover token, e.g: 56bf1f7e-ebdf-11e8-8afa-005056ab4d6f
        """
        logging.info("Retrieving details for handover " + str(handover_token))
        r = requests.get(self.handover_token.format(self.uri,str(handover_token)))
        r.raise_for_status()
        return r.json()

    def handover_summary_email(self, handovers, email):
        """
        Retrieve all the handovers associated with a given email
        Generate a unique list of handed over databases
        If a database was handed over multiple times, the latest one will be displayed.
        Print everything
        """
        fail_pattern = re.compile(".*(failed|problems).*")
        successful_pattern = re.compile(".*successful.*")
        summary={}
        logging.info("Retrieving handovers for " + str(email))
        for handover in handovers:
            if handover['contact'] == email:
                src_uri = make_url(handover['src_uri'])
                if src_uri.database not in summary:
                    summary[src_uri.database] = handover
        for sum in summary:
            handover_result = "in progress"
            if fail_pattern.match(summary[sum]['current_message']):
                handover_result = "failed"
            elif successful_pattern.match(summary[sum]['current_message']):
                handover_result = "success"
            logging.info("Handover %s - %s : %s" % (summary[sum]['handover_token'],sum, handover_result))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Handover a database via a REST service')
    parser.add_argument('-u', '--uri', help='HC REST service URI', required=True)
    parser.add_argument('-a', '--action', help='Action to take', choices=['submit', 'retrieve', 'list', 'delete', 'summary'], required=True)
    parser.add_argument('-v', '--verbose', help='Verbose output', action='store_true')
    parser.add_argument('-s', '--src_uri', help='URI of database to hand over')
    parser.add_argument('-e', '--email', help='Email address')
    parser.add_argument('-c', '--description', help='Description')
    parser.add_argument('-t', '--handover_token', help='Handover token')

    args = parser.parse_args()

    if args.verbose == True:
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')

    if args.uri.endswith('/') == False:
        args.uri = args.uri + '/'

    client = HandoverClient(args.uri)

    if args.action == 'submit':

        spec = {
            "src_uri" : args.src_uri,
            "contact" : args.email,
            "comment" : args.description
            }
        logging.debug(spec)
        handover_id = client.submit_handover(spec)
        logging.info('Job submitted with transaction ID '+str(handover_id))
    elif args.action == 'list':
        handovers = client.list_handovers()
        for handover in handovers:
            client.print_handover_detail(handover)
    elif args.action == 'retrieve':
        handover = client.retrieve_handover(args.handover_token)
        client.print_handover_detail(handover[0])
    elif args.action == 'summary':
        handovers = client.list_handovers()
        client.handover_summary_email(handovers,args.email)
    else:
        logging.error("Action "+args.action+" not supported")
