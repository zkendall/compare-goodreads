#-------------------------------------------------------------------------------
# Name:        Compare Goodreads
# Purpose:     See which friends your tastes best match
# Author:      Zachariah Kendall
# Notes:
#
#-------------------------------------------------------------------------------


# Imports and Configuration #
import logging
logging.basicConfig(filename='webapp.log',
                    level=logging.DEBUG,
                    format='%(asctime)s  %(levelname)s  ' +
                           '%(funcName)s():\t%(message)s',
                    datefmt='%m/%d %I:%M:%S'
                    )

import goodreads
import thread
import os
from math import sqrt
from flask import Flask, render_template, redirect, url_for, request, session, copy_current_request_context
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.debug = bool(os.environ.get('DEBUG'))

if not app.debug:
    app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')

# Temp
client = goodreads.Client(client_id=os.environ.get('CLIENT_ID'),
                          client_secret=os.environ.get('CLIENT_SECRET'))
if app.debug:
    client.authenticate(access_token=os.environ.get('ACCESS_TOKEN'),
                    access_token_secret=os.environ.get('ACCESS_TOKEN_SECRET'))


# Page Routes #

@app.route('/')
def index():
    ''' Starting point. '''
    logging.info('')
    return render_template('index.html')

@app.route('/graph/<id>')
def graph(id):
    '''
    Where the magic happens.
    ::id - user's goodread id
    '''
    logging.info('')
    return render_template('graph.html', id=id)

@app.route('/authenticate')
def authenticate():
    ''' '''

    if app.debug:
        id, name = client.get_auth_user()
        return redirect('goodreads_callback?oauth_token=l9RKYJCINDu4BhESAsXGbw&authorize=0')

    url = client.get_authentication_url()
    logging.info("Auth URL:" + str(url))

    # Reroute to goodreads for authentication
    return redirect(url)


@app.route('/goodreads_callback')
def goodreads_callback():
    '''
    Goodreads will redirect here after authentication.
    Sample: .com/goodreads_callback?oauth_token=l9RKYJCINDu4BhESAsXGbw&authorize=1
    '''
    # Get argument data from string
    oauth_token= request.args.get('oauth_token')
    authorize = request.args.get('authorize', 0)
    logging.info('Token: ' + oauth_token + ' authorize: ' + authorize)
    
    # Did user approve?
    if authorize == '1':
        client.finish_authentication()
    elif not app.debug:
        return redirect('/')

    logging.info('Finished Authentication')

    # Safe user in sessionlogged in user id/name session
    id, name = client.get_auth_user()
    session['goodreads_name'] = name
    session['goodreads_id'] = id

    # Initialize progress
    session['comparison_results'] = ''
    session['comparison_progress'] = 0

    # Start the comparison process in bg thread
    @copy_current_request_context
    def do_work():
        compare()
    thread.start_new_thread(do_work, ())

    return redirect('graph/'+id)

@app.route('/get_progress')
def get_progress():
    ''' Get the progress of the comparison opperation '''
    session['comparison_progress'] += 25
    return str(session['comparison_progress'])

@app.route('/get_results')
def get_results():
    ''' '''
    return open('results.tsv').read()

#--------------------------
#   Processing Methods
#--------------------------

def compare():
    ''' Do actual calculations. Should be threaded... '''
    logging.info('Starting comparison...')

    # RETURN FAKE DATA
    #session['comparison_results'] = open('results.tsv').read()
    return
    ########

    # END TEST

    id, name = client.get_auth_user()
    friends = client.get_friends(id)
    
    # Save friend count for progress bar
    total = len(friends)

    results = []
    for i, friend in enumerate(friends):
        session['comparison_progress'] = total / i
        f_id = friend[0] #id

        comparison = client.compare_books(f_id)
        correlation = compute_rating_correlation(comparison.reviews)

        logging.info(str(i) + ": " +(str(friend[1])) + ',' + str(correlation))

        results.append( (friend[1], correlation, len(reviews)) )

    session['comparison_results'] = make_tsv(results)

def make_tsv(data):
    ''' Convert results to tab spaced values to load into graph. '''
    tsv = 'Name\tPearsons\tBooks\n'
    for comparison in data:
        tsv += '{0}\t{1}\t{2}\n'.format(comparison[0], comparison[1], comparison[2])
    return tsv

def compute_rating_correlation(reviews):
    """
    Parse goodreads review comparison into list of (my rating, their rating)
    and pass to peason()
    Returns: distance
    """
    if len(reviews) < 1:
        return 0 # No correlation

    ratings = []
    for r in reviews:
        try:
            r1 = int(r['your_rating'])
            r2 = int(r['their_rating'])
        except ValueError:
            continue
        ratings.append((r1, r2))
    distance = pearson(ratings)
    return distance

def pearson(ratings):
    """ Computes the Pearson product-moment correlation coefficient.
    Modified from: guidetodatamining.com (Ron Zacharski) """
    if len(ratings) < 1:
        return 0

    sum_xy = sum_x = sum_y = sum_x2 = sum_y2 = n = 0
    for rating_pair in ratings:
        n += 1
        x = rating_pair[0]
        y = rating_pair[1]
        sum_xy += x * y
        sum_x += x
        sum_y += y
        sum_x2 += pow(x, 2)
        sum_y2 += pow(y, 2)
    # now compute denominator
    denominator = sqrt(sum_x2 - pow(sum_x, 2) / n) * sqrt(sum_y2 - pow(sum_y, 2) / n)
    if denominator == 0:
        return 0
    else:
        return (sum_xy - (sum_x * sum_y) / n) / denominator

#--------------------------
#
#--------------------------

if __name__ == '__main__':
    app.run()

