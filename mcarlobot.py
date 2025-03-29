'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

import random
import eval7

class Player(Bot):
    '''
    A pokerbot.
    '''
    
    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        pass

    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        #my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        #game_clock = game_state.game_clock  # the total number of seconds your bot has left to play this game
        #round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        #my_cards = round_state.hands[active]  # your cards
        #big_blind = bool(active)  # True if you are the big blind
        pass

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        #my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        previous_state = terminal_state.previous_state  # RoundState before payoffs
        #street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        #my_cards = previous_state.hands[active]  # your cards
        #opp_cards = previous_state.hands[1-active]  # opponent's cards or [] if not revealed
        pass 

    def get_action(self, game_state: GameState, round_state: RoundState, active: int):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your action.
        '''
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot'

        if RaiseAction in legal_actions:
            min_raise, max_raise = round_state.raise_bounds()
            min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
            max_cost = max_raise - my_pip  # the cost of a maximum bet/raise
        
        
        ##########################
        #    P O S T F L O P     #
        ##########################         

        # hyperparameters
        BLUFF_FACTOR = .3
        GOOD_HAND_RAISE = .5
        BET_GOOD_HAND_RAISE = .7
        SIMULATIONS = 10000
        BORDER_CALL =.4

        equity = self.estimate_equity(my_cards, board_cards, 1, 90+90*int(street/2))
        
        
        
        rand_mix = random.random()
        bluff_factor = BLUFF_FACTOR * random.random()
        #            R A I S E          |            C H E C K 
        if(continue_cost == 0):
            if equity +bluff_factor> 0.6 and RaiseAction in legal_actions:
                raise_amount = min(max(int(min_raise * (.5 + equity)), min_raise), max_raise)

                if(rand_mix < GOOD_HAND_RAISE):
                    return RaiseAction(raise_amount)
                return CheckAction() if CheckAction in legal_actions else CallAction()
            else:
                return CheckAction() if CheckAction in legal_actions else CallAction()
        #            R A I S E    |      C A L L      |      F O L D
        if equity+bluff_factor > .6:
            if RaiseAction in legal_actions and rand_mix < BET_GOOD_HAND_RAISE:
                raise_amount = min(max(int(min_raise * (.5 + equity)), min_raise), max_raise)
        
                # raise 30% of time
                return RaiseAction(raise_amount)
            else:
                return CallAction()
        elif equity > BORDER_CALL:
            # borderline call
            # maybe call if cheap, else fold
            if continue_cost <= 15:
                return CallAction()
            else:
                return FoldAction()
        else:
            # not enough equity, so fold
            return FoldAction()

    def estimate_equity(self, my_cards, board_cards, opp_count=1, num_samples=150):
            '''
            Quick Monte Carlo equity approximation using eval7.
            
            my_cards: list of strings, e.g. ['Ah', 'Kd', '5s']
            board_cards: list of strings, e.g. ['2h', 'Td']
            opp_count: number of opponents (1 in B4G)
            num_samples: how many random draws for simulation
            '''
            deck = eval7.Deck()

            # remove our known cards + board cards from deck
            used_cards = my_cards + board_cards
            for c in used_cards:
                card = eval7.Card(c)
                deck.cards.remove(card)
            
            wins = 0
            # do repeated trials
            for _ in range(num_samples):
                deck.shuffle()
                # deal opponents cards
                opp_hole = deck.deal(3)
                # deal board coards
                remaining = 4 - len(board_cards)
                sim_board = [eval7.Card(c) for c in board_cards] + deck.deal(remaining)

                # eval hands
                my_score = eval7.evaluate(sim_board+ [eval7.Card(c) for c in my_cards])
                opp_scores = eval7.evaluate(sim_board + opp_hole)

                # determine wins
                if my_score > opp_scores:
                    wins += 1
                elif my_score == opp_scores:
                    wins += 0.5 

                # put cards back to deck for next iteration
                deck = eval7.Deck()
                for c2 in used_cards:
                    deck.cards.remove(eval7.Card(c2))
            # return ratio
            return wins / num_samples

if __name__ == '__main__':
    run_bot(Player(), parse_args())
