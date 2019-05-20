/*

choices[5] = "abcde"
children[5] = {130, 6, 16, 2483, 134}
values[5] = NULL // this word is illegal
choices[6] = "#ing" // "patricia trie" optimization -- TODO
children[6] = {9641}
values[6] = VALUE // this word is legal
*/
#include "stdafx.h"
#include "trie.h"
#define EMPTY_VALUE -1
#if !defined(WIN32) && !defined(MS_WINDOWS)
#define _TCHAR char*
#endif
//#define _DEBUG
//#undef _DEBUG

Node* _add_root_node(){
    Node* trie = malloc(sizeof(Node));
    trie->choices = NULL;
    trie->children = NULL;
    trie->value = EMPTY_VALUE;
    return trie;
}

int _add_choice(Node* node, const char chr){
    int insert_position;
    char* choices = node->choices;
    if(choices != NULL){
        insert_position = strlen(choices);
        choices = realloc(choices, (insert_position+2) * sizeof(*choices));
    }else{
        insert_position = 0;
        choices = malloc(2 * sizeof(*choices));
    }
    choices[insert_position] = chr;
    choices[insert_position+1] = 0;
    node->choices = choices;
    node->children = (Node*)realloc(node->children, (insert_position+1) * sizeof(*node->children));
    node->children[insert_position].choices = NULL;
    node->children[insert_position].children = NULL;
    node->children[insert_position].value = EMPTY_VALUE;
    return insert_position;
}

Trie* trie_create(){
    Trie* trie = malloc(sizeof(Trie));
    trie->root = _add_root_node();
    return trie;
}

int trie_find_word(Node *trie, const char* str){
    int last_branch=0, last_match=0;
    Node *next_pos = trie;
    const char* ptr = str;
    for(; *ptr; ptr++){
        if(!next_pos || !next_pos->choices){
            return ~(ptr-str);
        }else{ // trying prefixes
            char* choices = next_pos->choices;
            char* found = strchr(choices, *ptr);
            if(found == NULL){
                return ~(ptr-str);
            }else{
                last_branch = (found - choices) / sizeof(*choices);
                next_pos = next_pos->children + last_branch;
            }
        }
    }
    if(next_pos && next_pos->value != EMPTY_VALUE){
        return next_pos->value;
    }else{
        return ~(ptr-str); // not found, return processed length
    }
}

int* trie_find_prefixes(Node *trie, const char* str){
    int *target = malloc(sizeof(int) * (strlen(str)+2));
    int last_branch=0, last_match=0, counter=0;
    Node *next_pos = trie;
    const char* ptr = str;
    for(; *ptr; ptr++){
        if(!next_pos){
            target[0] = counter;
            return target;
        }else if(!next_pos->choices){
            target[++counter] = next_pos->value;
            target[0] = counter;
            return target;
        }else{ // trying prefixes
            char* choices = next_pos->choices;
            char* found = strchr(choices, *ptr);
            target[++counter] = next_pos->value;
            if(found == NULL){
                target[0] = counter;
                return target;
            }else{
                last_branch = (found - choices) / sizeof(*choices);
                next_pos = next_pos->children + last_branch;
            }
        }
    }
    if(next_pos){
        target[++counter] = next_pos->value;
    }
    target[0] = counter;
    return target;
}

Node* trie_add_word(Node *trie, const char* str){
    int last_branch=0;
    Node *next_pos = trie;
    const char* ptr;
    for(ptr = str; *ptr; ptr++){
        char* choices = next_pos->choices;
        char* found = NULL;
        if(choices != NULL){
            found = strchr(choices, *ptr);
        }
        if(found == NULL){
            last_branch = _add_choice(next_pos, *ptr);
        }else{
            last_branch = (found - choices) / sizeof(*choices);
        }
        next_pos = next_pos->children+last_branch;
    }
    return next_pos;
}


/**** Modification ****/
void c_has_prefix(){
    printf("%s\n", "has_prefix");
}

int contains_char(Node **ptr_node, int next){
    //printf("Contains_Char: %c\n", next);
    if(!ptr_node){ //
        return 0;
    }

    Node *node = *ptr_node;

    int last_branch=0;
    char* choices = node->choices;
    if (!choices){
        return 0; //you can return null as well
    }
    char* found = strchr(choices, next);
    if(found == NULL){
        return 0; // you can return null as well
    }
    last_branch = (found - choices) / sizeof(*choices);
    *ptr_node = (Node *)(node->children + last_branch);
    return 1;
    
}

void copy_to(Node **from_state, Node **to_state){
    memcpy(to_state, from_state, sizeof(Node*));
}

void node_print(Node **n){
    printf("%s\n", (*n)->choices);
}

Node** initialize_state(Node *s){
    Node **new = malloc(sizeof(Node*));
    copy_to(&s,new);
    return new;
}

int c_is_leaf(Node **ptr){
    if ((*ptr)->value == EMPTY_VALUE){
        return 0;
    }
    else{
        return 1;
    }
}
/**** Modification Ends****/

void _trie_print(Node* trie, int depth){
    if(trie && trie->choices){
        char* c;
        int i = 0, j;
        if(trie->value != -1){
            printf(" -> %d\n", trie->value);
        }
        for(c = trie->choices; *c; c++, i++){
            if(i || trie->value != -1){
                for(j=0; j<depth; j++){
                    printf(".");
                }
            }
            printf("%c", *c);
            _trie_print(trie->children+i, depth+1);
        }
    }else{
        if(trie->value != -1){
            printf(" -> %d\n", trie->value);
        }
    }
}

void trie_print(Node* node){
    _trie_print(node, 0);
}

void trie_delete(Node* node){
    if(node){
        Node* next = node->children;
        char* c = node->choices;
        if(c){
            for(; *c; c++, next++){
                if(next->choices != NULL){
                    trie_delete(next);
                }
            }
            free(node->choices);
            free(node->children);
        }
    }
}

void trie_destroy(Trie* trie){
    trie_delete(trie->root);
    free(trie->root);
    trie->root = NULL;
}

int node_size(Node* node){
    if(node->choices){
        int i, len_choices=strlen(node->choices), sum=1;
        if(node->children){
            for(i=0; i<len_choices; i++){
                Node* next = node->children + i;
                sum += node_size(next);
            }
        }
        return sum;
    }
    return node != NULL;
}

int node_save(Node* node, char* stream){ // returns offset
    //Order: VALUE, choices, [save(c) for c in children]
    int offset = 0;
    if(node){
        if(stream){
            memcpy(stream+offset, &node->value, sizeof(node->value));
        }
        offset += sizeof(node->value);
        if(node->choices){
            int i, len = strlen(node->choices);
            if(stream){
                memcpy(stream+offset, node->choices, len+1);
            }
            offset += len + 1;
            for(i=0; i<len; i++){
                Node* subnode = NULL;
                if(node->children){
                    subnode = node->children + i;
                }else{
                }
                if(stream){
                    offset += node_save(subnode, stream + offset);
                }else{
                    offset += node_save(subnode, NULL);
                }
            }
        }else{
            if(stream){
                *(stream+offset) = 0;
            }
            offset += 1;
        }
    }else{
#ifdef _DEBUG
        printf("Saving NULL node!\n");
        fflush(stdout);
#endif
    }
    return offset;
}

SerialTrie* trie_save(Node* root){
    SerialTrie* st = malloc(sizeof(SerialTrie));
    char* stream;
    int actual;
    st->nodes = node_size(root);
    st->size = node_save(root, NULL);
    st->chars = st->size - st->nodes * sizeof(int); // st->chars == st->nodes * 2 - 1 by now
    //printf("Saving: %d bytes, %d chars, %d nodes\n", st->size, st->chars, st->nodes);
    st->size += 3 * sizeof(int);
    st->stream = malloc(st->size);
    stream = st->stream;
    memcpy(stream, &st->size , sizeof(int)); stream += sizeof(int);
    memcpy(stream, &st->nodes, sizeof(int)); stream += sizeof(int);
    memcpy(stream, &st->chars, sizeof(int)); stream += sizeof(int);
    actual = node_save(root, stream) + 3 * sizeof(int);
#ifdef _DEBUG
    printf("Expected: %d, Actual: %d\n", st->size, actual);
#endif
    return st;
}

typedef struct LoadPosition{
    char* chars;
    Node* root;
} LoadPosition;

int node_load(Node* node, LoadPosition *position, char* stream){ // returns offset
    int offset = 0;
    memcpy(&node->value, stream + offset, sizeof(node->value));
    offset += sizeof(node->value);
    if(*(stream+offset)){
        int i, len = strlen(stream + offset);
        memcpy(position->chars, stream + offset, len + 1);
        offset += len + 1;
        
        node->choices = position->chars;
        node->children = position->root;

        position->chars += len + 1;
        position->root += len;
        
        for(i=0; i<len; i++){
            Node* child = node->children+i;
            offset += node_load(child, position, stream+offset);
        }
    }else{
        node->children = NULL;
        node->choices = NULL;
        offset += 1;
    }
    return offset;
}

FrozenTrie* trie_load(char* stream){
    LoadPosition lp;
    Node* root;
    FrozenTrie* ftrie = malloc(sizeof(FrozenTrie));
    unsigned int node_offset, char_offset;
    int size          = *(int*)stream; stream += sizeof(int);
    ftrie->node_count = *(int*)stream; stream += sizeof(int);
    ftrie->char_count = *(int*)stream; stream += sizeof(int);
#ifdef _DEBUG
    printf("Loading: %d bytes, %d chars, %d nodes\n", size, ftrie->char_count, ftrie->node_count);
#endif
    fflush(stdout);
    ftrie->root = malloc(ftrie->node_count * sizeof(Node));
    ftrie->chars = malloc(ftrie->char_count);
    lp.root = ftrie->root;
    lp.chars = ftrie->chars;
    root = lp.root++;
    size -= node_load(root, &lp, stream);
    assert(size == 12);
    node_offset = lp.root - ftrie->root;
    char_offset = lp.chars - ftrie->chars;
    assert(ftrie->char_count >= char_offset);
    assert(ftrie->node_count == node_offset);
    return ftrie;
}

int trie_size(Node* root){
    return node_size(root) - 1;
}

void trie_fsck(Trie* trie){
    node_size(trie->root);
}

void test_create(){
    Trie *trie = trie_create(0);
    trie_fsck(trie);
}

void assert_not_found(Trie* trie, char* word, int expected_len){
    int actual, found = trie_find_word(trie->root, word);
    assert(found < 0);
    actual = ~found;
    printf("Expected: max prefix length %d for word %s, actual %d ... ", expected_len, word, actual);
    if(actual != expected_len){
        printf("Failed.\n");
    }else{
        printf("Passed.\n");
    }
    assert(actual == expected_len);
}

void assert_found(Trie* trie, char* word, int correct){
    int position;
    printf("Expected: word %s in trie, got ", word);
    position = trie_find_word(trie->root, word);
    if(position >= 0){
        printf("position: %d\n", position);
    }else{
        printf("error: %d\n", ~position);
    }
    assert(position == correct);
}

int *trie_find_splits(Node* prefix_root, Node* suffix_root, char* key){
    int i, s=0, l = strlen(key);
    int *prefixes = trie_find_prefixes(prefix_root, key);
    int *suffixes, *results, p0, s0, pi, res_len;
    // { doing key2 = strrev(key)
    char* key2 = malloc(sizeof(char)*(l+1));
    for(i=0; i<l; i++) {
        key2[l-i-1] = key[i];
    }
    key2[l] = 0;
    // }
    suffixes = trie_find_prefixes(suffix_root, key2);
    p0 = prefixes[0];
    s0 = suffixes[0];
    res_len = (p0 - (l-s0+1));
    if(res_len <= 0)
        res_len = 0;
    results = malloc(sizeof(int)*(res_len*3+1));
#ifdef _DEBUG
    printf("p0: %d, s0: %d, res_len: %d\n", p0, s0, res_len);
#endif
    for(pi = l-s0+1; pi < p0; pi++){ // l - i < s0 => i > l - s0
        int si = l-pi;
        if(prefixes[pi+1] != -1 && suffixes[si+1] != -1){
            results[s*3+1] = pi;
            results[s*3+2] = prefixes[pi+1];
            results[s*3+3] = suffixes[si+1];
            s++;
        }
    }
    free(key2);
    free(prefixes);
    free(suffixes);
    results[0] = s;
    return results;
}

int _tmain(int argc, _TCHAR* argv[])
{
    char * words[100] = {
        "abstract", "boolean", "break", "byte", "case", "catch", "char", "class",
        "const", "continue", "debugger", "default", "delete", "do", "double", "else", 
        "enum", "export", "extends", "false", "finally", "final", "float", "for", 
        "function", "goto", "if", "implements", "import", "in", "instanceof", "int", 
        "interface", "long", "native", "new", "null", "package", "private", "protected", 
        "public", "return", "short", "static", "super", "switch", "synchronized", 
        "this", "throw", "throws", "transient", "true", "try", "typeof", "var", "void",
        "volatile", "while", "with", 
        "a", "ab", "abst", "234", 0
    };
    int i;
    Node* id;
    Trie *trie = trie_create(0);
    trie_fsck(trie);
    //for(i=0; words[i]; i++){
    for(i=0; words[i]; i++){
        char* rev = words[i];
        //rev = _strdup(words[i]);
        //_strrev(rev);
        id = trie_add_word(trie->root, rev);
        id->value = i;
    }
    id = trie_add_word(trie->root, "class");
    assert(id->value == 7);

    trie_fsck(trie);
    trie_print(trie->root);

    assert_not_found(trie, "abs", 3);
    assert_not_found(trie, "apple", 1);
    assert_not_found(trie, "breaks", 5);
    assert_not_found(trie, "finall", 6);
    assert_not_found(trie, "123", 0);

    for(i=0; words[i]; i++){
        assert_found(trie, words[i], i);
    }

    {
        SerialTrie* strie = trie_save(trie->root);
        FrozenTrie* trie = trie_load(strie->stream);
    }

    {
        int* prefixes = trie_find_prefixes(trie->root, "abstracted");
        int i, correct_prefixes[] = {9, -1, 59, 60, -1, 61, -1, -1, -1, 0};
        for(i=0; i<correct_prefixes[0]; i++){
            assert(correct_prefixes[i] == prefixes[i]);
        }
    }
    {
        int* prefixes = trie_find_prefixes(trie->root, "hack");
        assert(prefixes[0] == 1);
        assert(prefixes[1] == -1);
    }
    {
        int* prefixes = trie_find_splits(trie->root, trie->root, "enumfi");
        int i, correct_prefixes[] = {1, 4, 16, 26};
        for(i=0; i<correct_prefixes[0]*3+1; i++){
            assert(prefixes[i] == correct_prefixes[i]);
        }
    }
    {
        int* prefixes = trie_find_splits(trie->root, trie->root, "intba");
        int i, correct_prefixes[] = {1, 3, 31, 60};
        for(i=0; i<correct_prefixes[0]*3+1; i++){
            assert(prefixes[i] == correct_prefixes[i]);
        }
    }
    {
        int* prefixes = trie_find_splits(trie->root, trie->root, "intsba");
        int i, correct_prefixes[] = {1, 2, 29, 61};
        for(i=0; i<correct_prefixes[0]*3+1; i++){
            assert(prefixes[i] == correct_prefixes[i]);
        }
    }
    {
        int* prefixes = trie_find_splits(trie->root, trie->root, "abstracttcartsba");
        int i, correct_prefixes[] = {1, 8, 0, 0};
        for(i=0; i<correct_prefixes[0]; i++){
            assert(prefixes[i] == correct_prefixes[i]);
        }
    }
    {
        int* prefixes = trie_find_splits(trie->root, trie->root, "implementsba");
        int i, correct_prefixes[] = {1, 10, 27, 60};
        for(i=0; i<correct_prefixes[0]; i++){
            assert(prefixes[i] == correct_prefixes[i]);
        }
    }
    return 0;
}
