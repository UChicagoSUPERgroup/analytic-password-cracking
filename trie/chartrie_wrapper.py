import chartrie

class CharTrieWrapper():
    """
    Wrapper for DATrie Library
    reference: https://github.com/pytries/datrie/tree/master/src
    """

    def __init__(self, wordlist):
        """
        Initialize a DATrie, given a wordlist addr. Read the wordlist and build the trie.
        """
        tmp = chartrie.CharTrie()
        for word in wordlist.keys():
            if word == "":
                continue
            tmp[bytes(word.encode())] = 0
        
        stream = tmp.dumps()
        f = open('dump.trie', 'wb')
        f.write(stream)
        f.close()
        trie = chartrie.FrozenCharTrie()
        trie.loads(stream)
        self.trie = trie

    def find(self, token_str):
        """
        Given a token_str, return all the keys that are contained by the trie.
        A token_str here is a list of sets. [set(a,b), set(b,c), etc...]
        """
        out = []
        q = []
        q.append((chartrie.TrieState(self.trie), 0, []))
        while (len(q) != 0):
            current_state, token_idx, trace = q.pop(0)
            current_save = chartrie.TrieState(self.trie)
            current_state.copy_to_state(current_save)
            for c in token_str[token_idx].get_value():
                if current_save.contains_next(c):
                    if token_idx == len(token_str) - 1:
                        if current_save.is_leaf():
                            #print("".join(trace+[c]))
                            out.append("".join(trace+[c]))
                            pass
                    else:
                        q.append((current_save, token_idx + 1, trace+[c]))
                        # For Efficiency Reasons
                    
                    current_save = chartrie.TrieState(self.trie)
                    current_state.copy_to_state(current_save)
        return out
