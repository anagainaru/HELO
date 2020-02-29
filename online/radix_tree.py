from collections import deque
import string

class RadixTree:
    def __init__(self):
        """
        Create a Radix Tree with only the default node root.
        """
        self.root = RadixTreeNode()
        self.root.key = ""
        self.size = 0


    def find_wildcard_pos(self,start_pos, key):
	while True:
		pos = [key.find("*",start_pos), key.find("d+",start_pos),key.find("n+",start_pos)]
		idx = [i for i in range(len(pos)) if pos[i]>=0 and pos[i]==min([j for j in pos if j>=0])]
		if len(idx)==0:
			break
		pos = pos[idx[0]]
		idx = idx[0]
		start_pos = pos+1

		hybrid = [".", "=", ":", "-", "(", "["," "]
		if idx==0:
			if pos>0:
				if key[pos-1] not in hybrid:
					continue
			if pos<len(key)-1:
				if key[pos+1]!=" ":
					continue
		elif idx==1:
			if pos>0:
				if key[pos-1] not in hybrid:
					continue
			if pos<len(key)-2:
				if key[pos+2]!=" ":
					continue
		elif idx==2:
			if pos>0:
				if key[pos-1]!=" ":
					continue
			if pos<len(key)-2:
				if key[pos+2]!=" ":
					continue		
		return (pos, idx)	
	return (-1,-1)

    def check_wildcards(self,n, node, new_text, number_of_matching_chars, key, value):
#	pos = [key.find("*",number_of_matching_chars), key.find("d+",number_of_matching_chars),key.find("n+",number_of_matching_chars)]
#	idx = [i for i in range(len(pos)) if pos[i]>=0 and pos[i]==min([j for j in pos if j>=0])]
#	if len(idx)==0:
#		return -1
#	pos = pos[idx[0]]
#	print "Pos",pos, idx[0],number_of_matching_chars,key
	ret = self.find_wildcard_pos(number_of_matching_chars, key)
	pos = ret[0]
	idx = ret[1]
	if pos==-1:
		return -1
	if pos>-1:
		if number_of_matching_chars==pos:
			n = node
		else:
#			print "1",key[number_of_matching_chars:pos]
			n.key = key[number_of_matching_chars:pos]
			node.real = False
			node.children.append(n)

		while pos>=0:
#			pos2 = [key.find("*",pos+1), key.find("d+",pos+1),key.find("n+",pos+1)]
#			idx2 = [i for i in range(len(pos2)) if pos2[i]>=0 and pos2[i]==min([j for j in pos2 if j>=0])]
#			if len(idx2)==0:
#				break
#			pos2 = pos2[idx2[0]]
			ret = self.find_wildcard_pos(pos+1, key)
			pos2 = ret[0]
			idx2 = ret[1]
			if pos2==-1 or pos+1==pos2:
				break
			if idx==0:
				delay = 1
			else:
				delay = 2
#			print "2",key[pos:pos+delay]
			n1 = RadixTreeNode()
		        n1.key = key[pos:pos+delay]
		        n1.real = False		
		        n1.value = value
			n.children.append(n1)
			n=n1
#			print "3",key[pos+delay:pos2]
	                n1 = RadixTreeNode()
	                n1.key = key[pos+delay:pos2]
	                n1.real = False		
	                n1.value = value
			n.children.append(n1)
			n=n1
			pos = pos2
			idx = idx2

		if idx==0:
			delay = 1
		else:
			delay = 2
#		print "4",key[pos:pos+delay],"---",idx,delay
		n1 = RadixTreeNode()
	        n1.key = key[pos:pos+delay]
	        n1.real = True
		if pos+2<len(key)-1:
			n1.real = False
	        n1.value = value
		n.children.append(n1)
		n=n1
		if pos+2<len(key)-1:
#			print "5",key[pos+delay:]
			n1 = RadixTreeNode()
		        n1.key = key[pos+delay:]
		        n1.real = True		
		        n1.value = value
			n.children.append(n1)
	else:
		return -1
	return pos

    def insert(self, key, value, node=None):
#	print "insert",key,value
        """
        Recursively insert the key in the radix tree
        """
        if not node:
            node = self.root
            self.size += 1

        number_of_matching_chars = node.get_number_of_matching_characters(key)
	#print
	#print "KEY",key,"matching",number_of_matching_chars,"det",node.key

        # we are either at the root node
        # or we need to go down the tree
        if node.key == "" or number_of_matching_chars == 0 or (
        number_of_matching_chars < len(key) and number_of_matching_chars >= len(node.key)):
            flag = False
            new_text = key[number_of_matching_chars:]
            for child in node.children:
		if child.key == "d+":
			continue
                if child.key.startswith(new_text[0]) and new_text[:2]!="d+" and new_text[:2]!="n+":
                    flag = True
		    #print "insert nou --",new_text
                    self.insert(new_text, value, child)
                    break

            # just add the node as the child of the current node
            if not flag:
                n = RadixTreeNode()
                n.key = new_text
                n.real = False
                n.value = value

		# check for wildcards
		pos = self.check_wildcards(n, node, new_text, number_of_matching_chars, key, value)
		if pos==-1:
			n.real = True
	                node.children.append(n)

		#print "append --",new_text

        # there is an exact match, just make the current node a data node
        elif number_of_matching_chars == len(key) and number_of_matching_chars == len(node.key):
            if node.real:
		return
                #raise DuplicateKeyError("Duplicate Key: '%s' for value: '%s' " % (key, node.value))

            node.real = True
            node.value = value

        # this node needs to be split as the key to be inserted
        # is a prefix of the current node key
        elif number_of_matching_chars > 0 and number_of_matching_chars < len(node.key):
            n1 = RadixTreeNode()
            n1.key = node.key[number_of_matching_chars:]
            n1.real = node.real
            n1.value = node.value
            n1.children = node.children

            node.key = key[0:number_of_matching_chars]
            node.real = False
            node.children = [n1]

	    #print "split children --",key[0:number_of_matching_chars],"--",key[number_of_matching_chars:]
            if number_of_matching_chars < len(key):
                n2 = RadixTreeNode()
                n2.key = key[number_of_matching_chars:]
                n2.real = False
                n2.value = value

		pos = self.check_wildcards(n2, node, key[number_of_matching_chars:], 0, key[number_of_matching_chars:], value)
		if pos==-1:
			n2.real = True
	                node.children.append(n2)
#                node.children.append(n2)

            else:
                node.value = value
                node.real = True

        # this key needs to be added as the child of the current node
        else:
            n = RadixTreeNode()
            n.key = node.key[number_of_matching_chars:]
            n.children = node.children
            n.real = node.real
            n.value = node.value

            node.key = key
            node.real = True
            node.value = value
            node.children.append(n)
	    #print "append as child --",node.key[number_of_matching_chars:]


    def delete(self, key):
        """
        Deletes the key from the trie
        """
        visitor = VisitorDelete()

        self.visit(key, visitor)

        if (visitor.result):
            self.size -= 1

        return visitor.result


    def find(self, key):
        """
        Returns the value for the given key
        """
        visitor = VisitorFind()

        self.visit(key, visitor)

        return visitor.result

    def complete(self, key, node=None, base=""):
        """
        Complete the a prefix to the point where ambiguity starts.

        Example:
        If a tree contain "blah1", "blah2"
        complete("b") -> return "blah"

        Returns the unambiguous completion of the string
        """
        if not node:
            node = self.root

        i = 0
        key_len = len(key)
        node_len = len(node.key)

        while i < key_len and i < node_len:
            if key[i] != node.key[i]:
                break

            i += 1

        if i == key_len and i <= node_len:
            return base + node.key

        elif node_len == 0 or (i < key_len and i >= node_len):
            beginning = key[0:i]
            ending = key[i:key_len]
            for child in node.children:
                if child.key.startswith(ending[0]):
                    return self.complete(ending, child, base + beginning)

        return ""

    def search_prefix(self, key, record_limit):
        """
        Returns all keys for the given prefix
        """
        keys = []

        node = self._search_prefix(key, self.root)

        if node:
            if node.real:
                keys.append(node.value)
            self.get_nodes(node, keys, record_limit)

        return keys

    def _search_prefix(self, key, node):
        """
        Util for the search_prefix function
        """
        result = None

        number_of_matching_chars = node.get_number_of_matching_characters(key)

        if number_of_matching_chars == len(key) and number_of_matching_chars <= len(node.key):
            result = node

        elif node.key == "" or (number_of_matching_chars < len(key) and number_of_matching_chars >= len(node.key)):
            new_text = key[number_of_matching_chars:]
            for child in node.children:
                if child.key.startswith(new_text[0]):
                    result = self._search_prefix(new_text, child)
                    break

        return result

    def get_nodes(self, parent, keys, limit):
        """
        Updates keys... (not really sure)
        """
        queue = deque(parent.children)

        while len(queue) != 0:
            node = queue.popleft()
            if node.real:
                keys.append(node.value)

            if len(keys) == limit:
                break

            queue.extend(node.children)


    def visit(self, prefix, visitor, parent=None, node=None):
        """
        Recursively visit the tree based on the supplied "key". Calls the Visitor
        for the node those key matches the given prefix
        """
        if not node:
            node = self.root

        number_of_matching_chars = node.get_number_of_matching_characters(prefix)

        # if the node key and prefix match, we found a match!
        if number_of_matching_chars == len(prefix) and number_of_matching_chars == len(node.key):
            visitor.visit(prefix, parent, node)

        # we are either at the root OR we need to traverse the children
        elif node.key == "" or (number_of_matching_chars < len(prefix) and number_of_matching_chars >= len(node.key)):
            new_text = prefix[number_of_matching_chars:]
            for child in node.children:
                # recursively search the child nodes
                if child.key.startswith(new_text[0]):
                    self.visit(new_text, visitor, node, child)
                    break


    def contains(self, key):
        """
        Returns True if the key is valid. False, otherwise.
        """
        visitor = VisitorContains()
        self.visit(key, visitor)
        return visitor.result

    def debug(self):
        """
        Returns a string representation of the radix tree.
        WARNING: Do not use on large trees!
        """

        lst = []
        self._debug_node(lst, 0, self.root)
	#for i in lst:
	#	print i

        return "\n".join(lst)

    def _debug_node(self, lst, level, node):
        """
        Recursive utility method to generate visual tree
        WARNING: Do not use on large trees!
        """

#	print "in node", node.key, node.value

        temp = " " * level
        temp += "|"
        temp += "-" * level

        if node.real:
            temp += "%s[%s]" % (node.key, node.value)
	    #print node.parent.key
        else:
            temp += "%s" % (node.key)

        lst.append(temp)
#	print temp

        for child in node.children:
#	    print "parse child",child.key, child.value
            self._debug_node(lst, level + 1, child)



    def HELO_match(self, key):
	#print key
	desc =""
        ret = self._match_node(self.root, key, desc)
        return ret

    def _match_node(self, node, key, desc):
	start=0
	if node.key!="":
  	    #print "in node",node.key, "-",key		
	    fnd=0
	    # check if the current node is a wild card
	    if node.key=="*":
		start = key.find(" ")
		fnd=1
	    if node.key=="d+" and fnd==0:
		try:
			aux=int(key[0])
			start = key.find(" ")
			fnd=1
		except:
			pass
	    if node.key=="n+":
		return (node.value, desc+node.key)
	    if fnd==0:
		if len(node.key)>len(key):
			return (-1,"")
		if node.key != key[:len(node.key)]:
			return (-1,"")
	
	    if fnd==0 and node.real and len(key)==len(node.key):
		return (node.value, desc+node.key)
            if fnd==1 and node.real and key.find(" ")<0:
		return (node.value, desc+node.key)

	if start==0:
		start = len(node.key)
	desc = desc+node.key
        for child in node.children:
            ret = self._match_node(child, key[start:], desc)
	    if ret[0]>-1:
		return ret
	return (-1, "")


    def HELO_contains_tempID(self, value):
	#print key
        ret = self._contains_value(self.root, value)
        return ret

    def _contains_value(self, node, value):
        if node.real:
            if node.value == value:
		return True
        for child in node.children:
            ret = self._contains_value(child, value)
	    if ret==True:
		return True
	return False


    def HELO_delete_tempID(self, value):
	#print key
        ret = self._delete_value(self.root, value)
        return ret

    def _delete_value(self, node, value):
        if node.real:
            if node.value == value:
		if len(node.children)>0:
			node.value=node.children[0].value
			node.real = False
			# merge the keys
			if len(node.children)==1:
				chstr = node.children[0].key
				if chstr!="*" and chstr!="d+" and chstr!="n+":
					node.key = node.key+chstr
					node.real = True
					del node.children[0]
			return 2
		return 1

        for i in range(len(node.children)):
	    child = node.children[i]
            ret = self._delete_value(child, value)
	    if ret==2:
		return 2
	    if ret==1: 
		del node.children[i]
		if len(node.children)==0:
			node.real = True
			return 1
		return 2
	return 3


    def HELO_modify_tempID(self, value, key):
        self._delete_value(self.root, value)
	self.insert(key, value)



class RadixTreeNode(object):
    def __init__(self):
        self.key = ""
        self.children = []
        self.real = False
        self.value = None

    def get_number_of_matching_characters(self, key):
        number_of_matching_chars = 0

        while number_of_matching_chars < len(key) and number_of_matching_chars < len(self.key):
            if key[number_of_matching_chars] != self.key[number_of_matching_chars]:
		if key[number_of_matching_chars]=="+" and (key[number_of_matching_chars-1]=="d" or key[number_of_matching_chars-1]=="n"):
			number_of_matching_chars = number_of_matching_chars - 1
                if self.key[number_of_matching_chars]=="+" and (self.key[number_of_matching_chars-1]=="d" or self.key[number_of_matching_chars-1]=="n"):
                        number_of_matching_chars = number_of_matching_chars - 1
                break
            number_of_matching_chars += 1

        return number_of_matching_chars


class Visitor(object):
    def __init__(self, initial_value=None):
        self.result = initial_value

    def visit(self, key, parent, node):
        pass


class VisitorFind(Visitor):
    def visit(self, key, parent, node):
        if node.real:
            self.result = node.value


class VisitorContains(Visitor):
    def visit(self, key, parent, node):
        self.result = node.real


class VisitorDelete(Visitor):
    def visit(self, key, parent, node):
        self.result = node.real

        # if it is a real node
        if self.result:
            # If there are no node children we need to
            # delete it from its parent's children list
            if len(node.children) == 0:
                for child in parent.children:
                    if child.key == node.key:
                        parent.children.remove(child)
                        break

                # if the parent is not a real node and there
                # is only one child then they need to be merged
                if len(parent.children) == 1 and not parent.real:
                    self.merge_nodes(parent, parent.children[0])

            # we need to merge the only child of this node with itself
            elif len(node.children) == 1:
                self.merge_nodes(node, node.children[0])

            # we just need to mark the node as non-real
            else:
                node.real = False

    def merge_nodes(self, parent, child):
        """
        Merge a child into its parent node. The operation is only valid if it is
        the only child of the parent node and parent node is not a real node.
        """
        parent.key += child.key
        parent.real = child.real
        parent.value = child.value
        parent.children = child.children


class DuplicateKeyError(Exception):
    pass


if __name__ == "__main__":
    rt = RadixTree()

    rt.insert("data * : unknown user: * * n+", 1)
    rt.insert("data * : unknown user: * * n+", 1)
    rt.insert("d+ from *", 2)
    rt.insert("identification d+ from *", 3)
    rt.insert("identity modified * 124", 4)
    rt.insert("identification data * 123 port", 5)

#    rt.insert("* on /dev/pts/19", 5)
#    rt.insert("* : tty=* ; pwd=* ; user=root ; command=* * *", 6)
#    rt.insert("* listening on * * n+", 7)
#    rt.insert("* as root: cmd=* n+", 8)
#    rt.insert("- * * n+", 9)
#    rt.insert("***",10)

#    print(rt.debug())

    print
    print "Contains"
    print rt.HELO_contains_tempID(3)
    print rt.HELO_contains_tempID(18)
    print

    #rt.HELO_modify_tempID(11,"* on /dev/pts/16")

    print(rt.debug())

    print rt.HELO_match("data hvv : unknown user: gcvgv")
    print rt.HELO_match("5 from 7")
    print rt.HELO_match("identification data 5 123 port")
    print rt.HELO_match("identification 5 from ana")
   # print rt.HELO_match("ana on /dev/pts/16")
   # print rt.HELO_match("ana on /dev/pts/19")
   # print rt.HELO_match("jhgjhj : tty=jhj ; pwd=nghfd6 ; user=root ; command=8ghfyf uguyg uuy")
   # print rt.HELO_match("jhghg listening on 6 7 0 0 8")
   # print rt.HELO_match("root@c11-10c1s2 as root: cmd='mv -f /var/tmp/l0state.c1s2.tmp.gz /var/tmp/l0state.c1s2.gz'")
   # print rt.HELO_match("- CURRENT SERVICE STATE:")
   # print rt.HELO_match("anaaremere")


