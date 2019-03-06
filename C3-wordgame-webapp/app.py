

import decimal
import enchant
import time

import data_utils
import word_utils

from flask import Flask, render_template, request, session, flash, redirect


# Before we do anything else, pre-process the words, then
# update our enchant dictionary.  We do this only ONCE.
# Yes, that's right: these are GLOBAL (shock! horror!).
word_utils.pre_process_words()
wordgame_dictionary = enchant.DictWithPWL('en_GB', word_utils.ALL_WORDS)


app = Flask(__name__)
app.secret_key = 'fhdgsd;ohfnvervneroigerrenverbner32hrjegb/kjbvr/o'


def check_spellings(words: list) -> list:
    """Check a list of words for spelling errors.

       Is the word in the dictionary.
       Accepts a list of words and returns a list of tuples,
       with each tuple containing (word, bool) based on
       whether or not the word is spelled correctly."""
    spellings = []
    for w in words:
        spellings.append((w, wordgame_dictionary.check(w)))
    return spellings


@app.route('/')
@app.route('/rules')
def welcome() -> 'html':
    return render_template('welcome.html',
                           title='Welcome to Word Game on the Web')


@app.route('/startgame')
def start_new_game() -> 'html':
    session['sourceword'] = word_utils.get_source_word()
    session['start_time'] = time.perf_counter()
    return render_template('startgame.html',
                           title="Let's get busy!",
                           sourceword=session['sourceword'])


@app.route('/processwords', methods=['POST'])
def process_the_words() -> 'html':
    session['end_time'] = time.perf_counter()
    we_have_a_winner = True
    seven_words = request.form['seven_words'].lower().split(' ')
    seven_words = [w for w in seven_words if len(w) >= 1]
    # Now that we have the data, let's perform the checks.
    nw = len(seven_words)
    if nw != 7:
        we_have_a_winner = False
        flash('You have an incorrect number of words: {}, not 7.'.format(nw))
    disallowed_letters = []
    for word in seven_words:
        disallowed = [letter for (letter, ok) in
                      word_utils.check_letters(session['sourceword'], word)
                      if not ok]
        disallowed_letters.extend(disallowed)
    if disallowed_letters:
        we_have_a_winner = False
        flash('You used these invalid letters: ' +
              ' '.join(set(disallowed_letters)))
    misspelt_words = [word for (word, ok) in
                      check_spellings(seven_words)
                      if not ok]
    if misspelt_words:
        we_have_a_winner = False
        flash('You misspelt these words: ' +
              ' '.join(sorted(misspelt_words)))
    short_words = [word for (word, ok) in
                   word_utils.check_size(seven_words)
                   if not ok]
    if short_words:
        we_have_a_winner = False
        flash('These words are too small: ' +
              ' '.join(sorted(short_words)))
    if word_utils.duplicates(seven_words):
        we_have_a_winner = False
        flash('You have duplicates in your list: ' +
              ' '.join(sorted(seven_words)))
    if word_utils.check_not_sourceword(seven_words, session['sourceword']):
        we_have_a_winner = False
        flash('You cannot use the source word: '+session['sourceword'])
    # With all the checks performed, how did we do?
    time_taken = round(session['end_time']-session['start_time'], 2)
    if time_taken < 5.0:
        we_have_a_winner = False
        flash("Skullduggery is afoot.  There's no way you were that quick!")
    if we_have_a_winner:
        session['how_long'] = str(time_taken)
        flash('Congratulations! You took '+session['how_long']+' seconds.')
        session['done'] = False
        return render_template('winner.html',
                               title="You're a winner!")
    else:
        return render_template('loser.html',
                               title='Better luck next time.')


@app.route('/processhighscore', methods=['POST'])
def record_high_score() -> 'html':
    if not session['done']:
        session['done'] = True
        user = request.form['username']
        how_long = float(session['how_long'])
        sw = session['sourceword']
        data_utils.add_to_scores(user, how_long, sw)
        board = data_utils.get_sorted_leaderboard()
        return render_template('leaderboard.html',
                               title='How did you do?',
                               leaderboard=board,
                               position=board.index((round(decimal.Decimal(how_long), 2), user, sw))+1,
                               outof=len(board))
    else:
        return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
