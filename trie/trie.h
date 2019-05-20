#pragma once
/*
choices[5] = "abcde"
choice_links[5] = {130, 6, 16, 2483, 134}
values[5] = NULL // if this word is illegal
values[6] = VALUE // if this word is legal
choices[6] = "#ing" // "patricia trie" optimization
choice_links[6] = {9641}
values[6] = VALUE
*/

#pragma pack(push,1)

typedef struct Node {
    int value;
    char *choices;
    struct Node* children;
} Node;

typedef struct Trie {
    Node* root;
} Trie;

typedef struct SerialTrie {
    Node* root;
    char* stream;
    int size; // == len(stream)
    int nodes;
    int chars;
} SerialTrie;

typedef struct FrozenTrie {
    Node* root;
    char* chars;
    unsigned int node_count; // == len(nodes)
    unsigned int char_count; // == len(chars)
} FrozenTrie;

Trie* trie_create();
int trie_find_word(Node *trie, const char* str);
Node* trie_add_word(Node *trie, const char* str);
int trie_size(Node* trie);
void trie_destroy(Trie *trie);
void trie_print(Node* trie);
int* trie_find_prefixes(Node *trie, const char* str);
int* trie_find_splits(Node* prefixes, Node* suffixes, char* key);
SerialTrie* trie_save(Node* trie);
FrozenTrie* trie_load(char* stream);

// modifications
void c_has_prefix();
int contains_char(Node **node, int next);
void copy_to(Node **from_state, Node **to_state);
void node_print(Node **n);
Node** initialize_state(Node *s);
int c_is_leaf(Node **ptr);

#pragma pack(pop)
