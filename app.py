import dis
import collections
import types
import inspect
import operator
import textwrap
import sys

def byteint(b):
    """Convert a byte to an integer."""
    return b if isinstance(b, int) else ord(b)

# what_to_execute = { "instructions": [("LOAD_VALUE", 0),
#     ("STORE_NAME", 0),
#     ("LOAD_VALUE", 1),
#     ("STORE_NAME", 1),
#     ("LOAD_NAME",0),
#     ("LOAD_NAME",1),
#     ("ADD_TWO_VALUES", None),
#     #("LOAD_VALUE", 2),
#     #("ADD_TWO_VALUES", None),
#     ("PRINT_ANSWER", None)],
# "numbers":[1, 2],
# "names":["a","b"]
# }

Block = collections.namedtuple("Block", "type, handler, stack_height")


class VirtualMachineError(Exception):
    pass

class VirtualMachine(object):
    def __init__(self):
        self.frames = []
        self.frame = None
        self.return_value = None
        self.last_exception = None

    def run_code(self, code, global_names=None, local_names=None):
        """ An entry point to execute code using the virtual machine"""
        frame = self.make_frame(code, global_names=global_names, local_names=local_names)
        self.run_frame(frame)

    def run_frame(self, frame):
        """Run a frame until it returns (somehow). Exceptions are raised, and the return value is returned."""

        self.push_frame(frame)

        while True:
            byte_name, arguments = self.parse_byte_and_args()

            # Add the following print statements
            print(f"Executing: {byte_name}, Arguments: {arguments}")
            print(f"Constants: {frame.code_obj.co_consts}")

            why = self.dispatch(byte_name, arguments)


    def top(self):
        return self.frame.stack.pop()
    
    def pop(self):
        return self.frame.stack.pop()
    
    def push(self, *vals):
        self.frame.stack.extend(vals)

    def popn(self, n):
        """Pop a number of values from the value stack.
        A list of 'n' values is returned , the deepest value first"""

        if n:
            ret = self.frame.stack[-n:]
            self.frame.stack[-n] = []
            return ret
        else:
            return []
        

    # def parse_byte_and_args(self):
    #     f = self.frame
    #     opoffset = f.last_instruction
    #     byteCode = byteint(f.code_obj.co_code[opoffset])
    #     f.last_instruction += 1
    #     byte_name = dis.opname[byteCode]
    #     if byteCode >= dis.HAVE_ARGUMENT:
    #         # index into the bytecode
    #         arg = f.code_obj.co_code[f.last_instruction:f.last_instruction+2]
    #         arg_val = byteint(arg[0]) + (byteint(arg[1]) << 8)

    #         print(arg_val)
    #         print(f.code_obj.co_consts)
    #         if byteCode in dis.hasconst: # Look up a constant
    #             arg = f.code_obj.co_consts[arg_val]
    #         elif byteCode in dis.hasname: # Look up a name
    #             arg = f.code_obj.co_names[arg_val]
    #         elif byteCode in dis.haslocal: # Look up a local name
    #             arg = f.code_obj.co_varnames[arg_val]
    #         elif byteCode in dis.hasjrel: # Calculate a relative jump
    #             arg = f.last_instruction + arg_val
    #         else:
    #             arg = arg_val
    #         argument = [arg]
    #     else:
    #         argument = []

    #     return byte_name, argument
    def parse_byte_and_args(self):
        f = self.frame
        opoffset = f.last_instruction
        byteCode = byteint(f.code_obj.co_code[opoffset])
        f.last_instruction += 1
        byte_name = dis.opname[byteCode]
    
        if byteCode >= dis.HAVE_ARGUMENT:
        # index into the bytecode
            arg = f.code_obj.co_code[f.last_instruction:f.last_instruction + 2]
            arg_val = byteint(arg[0]) + (byteint(arg[1]) << 8)

            print(f"byte_name: {byte_name}, arguments: {arg}")
            print(f"arg_val: {arg_val}, co_consts length: {len(f.code_obj.co_consts)}")


            if byteCode in dis.hasconst:  # Look up a constant
                arg = f.code_obj.co_consts[arg_val]
            elif byteCode in dis.hasname:  # Look up a name
                arg = f.code_obj.co_names[arg_val]
            elif byteCode in dis.haslocal:  # Look up a local name
                arg = f.code_obj.co_varnames[arg_val]
            elif byteCode in dis.hasjrel:  # Calculate a relative jump
                arg = f.last_instruction + arg_val
            else:
                arg = arg_val
            argument = [arg]
        else:
            argument = []

        return byte_name, argument





    def dispatch(self, byte_name, argument):
        """Dispatch by bytename to the corresponding methods. Exceptions are caught and set on the virtual machine"""

        #When later unwinding the block stack, we need to keep track of why we are doing it
        why = None
        try:
            bytecode_fn = getattr(self, 'byte_%s' % byte_name, None)
            if bytecode_fn is None:
                if byte_name.startswith('UNARY_'):
                    self.unaryOperator(byte_name[6:])
                elif byte_name.startswith('BINARY_'):
                    self.binaryOperator(byte_name[7:])
                else:
                    raise VirtualMachineError(
                        "unsupported bytecode type: %s" % byte_name
                    )
            else:
                why = bytecode_fn(*argument)
            
        except:
            #deal with exceptions encountered while executing the op.
            self.last_exception = sys.exc_info()[:2] + (None,)
            why = 'exception'

        return why
        
    # def run_frame(self, frame):
    #     """Run a frame unit it returns (somehow). exceptions are raised, the return value is returned."""

    #     self.push_frame(frame)

    #     while True:
    #         byte_name, arguments = self.parse_byte_and_args()

    #         why = self.dispatch(byte_name, arguments)

    #             #Deal with any block management we need to do
    #         while why and frame.block_stack:
    #             why = self.manage_block_stack(why)

    #         if why:
    #             break

    #     self.pop_frame()

    #     if why == 'exception':
    #         exc, val, tb = self.last_exception
    #         e = exc(val)
    #         e.__traceback__ = tb 
    #         raise e

    #     return self.return_value   

            #Frame manipulation
    def make_frame(self, code, callargs={}, global_names=None, local_names=None):
        if global_names is not None and local_names is not None:
            local_names = global_names
        elif self.frames:
            global_names = self.frame.global_names
            local_names = {}
        else:
            global_names = local_names = {
                '__builtins__' : __builtins__,
                '__name__' : '__main__',
                '__doc__' : None,
                '__package__' : None, #why ,
            }
        local_names.update(callargs)
        frame = Frame(code, global_names, local_names, self.frame)
        return frame

    def push_frame(self, frame):
        self.frames.append(frame)
        self.frame = frame

    def pop_frame(self):
        self.frames.pop()
        if self.frames:
            self.frame = self.frames[-1]
        else:
            self.frame = None

    def push_block(self, b_type, handler=None):
        stack_height = len(self.frame.stack)
        self.frame.block_stack.append(Block(b_type, handler, stack_height))

    def pop_block(self):
        return self.frame.block_stack.pop()
    
    def unwind_block(self, block):
        """Unwind the values on teh data stack corresponding to a given block."""
        if block.type == 'except-handler':
            #The exception itself is on the stack as type, value, and traceback.
            offset = 3
        else:
            offset = 0

        while len(self.frame.stack) > block.level + offset:
            self.pop()

        if block.type == 'except-handler':
            traceback, value, exctype = self.popn(3)
            self.last_exceptionast_exception = exctype, value, traceback

    def manage_block_stack(self, why):
        frame = self.frame
        block = frame.block_stack[-1]
        if block.type == 'loop' and why == 'continue':
            self.jump(self.return_value)
            why = None
            return why
        
        self.pop_block()
        self.unwind_block(block)

        if block.type == 'loop' and why == 'break':
            why = None
            self.jump(block.handler)
            return why
        
        if (block.type in ['setup-except', 'finally'] and why == 'exception'):
            self.push_block('except-handler')
            exctype, value, tb = self.last_exception
            self.push(tb, value, exctype)
            self.push(tb, value, exctype) #twice
            why = None
            self.jump(block.handler)
            return why
        
        elif block.type == 'finally':
            if why in ('retuen', 'continue'):
                self.push(self.return_value)

            self.push(why)

            why = None
            self.jump(block.handler)
            return why
        return why
    
    # def byte_LOAD_CONST(self, const):
    #     self.push(const)

    def byte_LOAD_CONST(self, const):
        try:
            const_value = self.frame.code_obj.co_consts[const]
            self.push(const_value)
        except TypeError:
            print(f"Error: TypeError in accessing co_consts. const: {const}, co_consts: {self.frame.code_obj.co_consts}")
            raise


    def byte_POP_TOP(self):
        self.pop()

    def byte_LOAD_NAME(self, name):
        frame = self.frame
        if name in frame.f_locals:
            val = frame.f_locals[name]
        elif name in frame.f_gloabls:
            val = frame.f_globals[name]
        elif name in frame.f_builtins:
            val = frame.f_builtins[name]
        else:
            raise NameError("name '%s' is not defined " % name)
        self.push(val)

    def byte_STORE_NAME(self, name):
        frame = self.frame
        if name in frame.f_locals:
            frame.f_locals[name] = self.pop()
        elif name in frame.f_globals:
            frame.f_globals[name] = self.pop()
        else:
            raise NameError("name '%s' is not defined " % name)


    def byte_LOAD_FAST(self, name):
        if name in self.frame.f_locals:
            val = self.frame.f_locals[name] 
        else:
            raise UnboundLocalError(
                "local variable '%s' referenced before assignment" % name
            )
        self.push(val)

    def byte_STORE_FAST(self, name):
        self.frame.f_locals[name] = self.pop()

    def byte_LOAD_GLOBAL(self, name):
        f = self.frame
        if name in f.f_gloabls:
            val = f.f_gloabls[name]
        elif name in f.f_builtins:
            val = f.f_builtins[name]
        else:
            raise NameError("global name '%s' is not defined" % name)
        self.push(val)


    BINARY_OPERATORS = {
        'POWER' : pow,
        'MULTIPLY' : operator.mul,
        'FLOOR_DIVIDE' : operator.floordiv,
        'TRUE_DIVIDE': operator.truediv,
        'MODULO' : operator.mod,
        'ADD': operator.add,
        'SUBTRACT': operator.sub,
        'SUBSCR' : operator.getitem,
        'LSHIFT' : operator.lshift,
        'RSHIFT': operator.rshift,
        'AND' : operator.and_,
        'XOR' : operator.xor,
        'OR': operator.or_
    }

    def binaryOperator(self, op):
        x, y = self.popn(2)
        self.push(self.BINARY_OPERATORS[op](x,y))

    COMPARE_OPERATORS = [
        operator.lt,
        operator.le,
        operator.eq,
        operator.ne,
        operator.gt,
        operator.ge,
        lambda x, y: x in y,
        lambda x, y: x not in y,
        lambda x, y: x is y,
        lambda x, y: x is not y,
        lambda x, y: issubclass(x, Exception) and issubclass(x,y),
    ]

    def byte_COMPARE_OP(self, opnum):
        x, y = self.popn(2)
        self.push(self.COMPARE_OPERATORS[opnum](x, y))


    def byte_LOAD_ATTR(self, attr):
        obj = self.pop()
        val = getattr(obj, attr)
        self.push(val)

    def byte_STORE_ATTR(self, name):
        val, obj = self.popn(2)
        setattr(obj, name, val)

    def byte_BUILD_LIST(self, count):
        elts = self.popn(count)
        self.push(elts)

    def byte_BUILD_MAP(self, size):
        self.push({})

    def byte_STORE_MAP(self):
        the_map, val, key = self.popn(3)
        the_map[key] = val
        self.push(the_map)

    def byte_LIST_APPEND(self, count):
        val = self.pop()
        the_list = self.frame.stack[-count]
        the_list.append(val)

    
    def byte_JUMP_FORWARD(self, jump):
        self.jump(jump)

    def byte_JUMP_ABSOLUTE(self, jump):
        self.jump(jump)

    def byte_POP_JUMP_IF_TRUE(self, jump):
        val = self.pop()
        if not val:
            self.jump(jump)

    def byte_SETUP_LOOP(self, dest):
        self.push_block('loop', dest)

    def byte_GET_ITER(self):
        self.push(iter(self.pop()))

    def byte_FOR_ITER(self, jump):
        iterobj = self.top()
        try:
            v = next(iterobj)
            self.push(v)
        except StopIteration:
            self.pop()
            self.jump(jump)

    def byte_MAKE_FUNCTION(self, argc):
        name = self.pop()
        code = self.pop()
        defaults = self.popn(argc)
        globs = self.frame.f_gloabls
        fn = Function(name, code, globs, defaults, None, self)
        self.push(fn)

    def byte_CALL_FUNCTION(self, arg):
        lenKw, lenPos = divmod(arg, 256) #!kwargs are not supported 
        posargs = self.popn(lenPos)

        func = self.pop()
        frame = self.frame
        retval = func(*posargs)
        self.push(retval)

    def byte_RETURN_VALUE(self):
        self.return_value = self.pop()
        return "return"

    


   








class Frame(object):
    def __init__(self, code_obj, global_names, local_names, prev_frame):
        self.code_obj = code_obj
        self.global_names = global_names
        self.local_names = local_names
        self.prev_frame = prev_frame
        self.stack = []
        if prev_frame:
            self.builtin_names = prev_frame.builtin_names
        else:
            self.builtin_names = local_names['__builtins__']
            if hasattr(self.builtin_names, '__dict__'):
                self.builtin_names = self.builtin_names.__dict__


        self.last_instruction = 0
        self.block_stack = []





class Function(object):
    """
    Create a realistic function object, defining the things the interpreter expects
    """
    __slots__ = [
        'func_code', 'func_name', 'func_defaults', 'func_globals',
        'func_locals', 'func_dict', 'func_closure',
        '__name__', '__dict__',
         # '__doc__',
        '_vm', '_func',
    ]

    def __init__(self, name, code, globs, defaults, closure, vm):
        self._vm = vm
        self.func_code = code
        self.func_name = self.__name__ = name or code.co_name
        self.func_defaults = tuple(defaults)
        self.func_globals = globs
        self.func_locals = self._vm.frame.f_locals
        self.__dict__ = {}
        self.func_closure = closure
        self.__doc__ = code.co_consts[0] if code.co_consts else None

        kw = {
            'argdefs' : self.func_defaults
        }
        if closure:
            kw['closure'] = tuple(make_cell(0) for _ in closure)
        self._func = types.FunctionType(code, globs, **kw)

    def __call__(self, *args, **kwargs):
        """when calling a function, make a new frame and run it."""
        callargs = inspect.getcallargs(self._func, *args, **kwargs)
        #Use callargs to provide a mapping of arguments : values to pass into the new frame
        frame = self._vm.make_frame(
            self.func_code, callargs, self.func_globals, {}
        )
        return self._vm.run_frame(frame)
    
    def make_cell(value):
        """Create a real python closure and grab a cell"""
        fn = (lambda x: lambda: x)(value)
        return fn.__closure__[0]

# class Interpreter:
#     def __init__(self):
#         self.stack = []
#         self.environment = {}

#     def STORE_NAME(self, name):
#         val = self.stack.pop()
#         self.environment[name] = val

#     def LOAD_NAME(self, name):
#         val = self.environment[name]
#         self.stack.append(val)


#     def parse_argument(self, instruction, argument, what_to_execute):
#         """ Understand whta the argument to each instruction means"""
#         numbers = ["LOAD_VALUE"]
#         names = ["LOAD_NAME", "STORE_NAME"]

#         if instruction in numbers:
#             argument = what_to_execute["numbers"][argument]
#         elif instruction in names:
#             argument = what_to_execute["names"][argument]

#         return argument
    
#     def LOAD_VALUE(self, number):
#         self.stack.append(number)

#     def PRINT_ANSWER(self):
#         answer = self.stack.pop()
#         print(answer)

#     def ADD_TWO_VALUES(self):
#         #first_num = self.stack.pop()
#         #second_num = self.stack.pop()
#         #total = first_num + second_num
#         #self.stack.append(total)
#         self.stack.append(self.stack.pop() + self.stack.pop())


#     def execute(self, what_to_execute):
#         instructions = what_to_execute["instructions"]
#         for each_step in instructions:
#             instruction, argument = each_step
#             argument = self.parse_argument(instruction=instruction, argument=argument, what_to_execute=what_to_execute)
#             # if instruction == "LOAD_VALUE":
#             #     self.LOAD_VALUE(argument)
#             # elif instruction == "ADD_TWO_VALUES":
#             #     self.ADD_TWO_VALUES()
#             # elif instruction == "STORE_NAME":
#             #     self.STORE_NAME(argument)
#             # elif instruction == "LOAD_NAME":
#             #     self.LOAD_NAME(argument)
#             bytecode_method = getattr(self, instruction)
#             if argument is None:
#                 bytecode_method()
#             else:
#                 bytecode_method(argument)
            
#             # elif instruction == "PRINT_ANSWER":
#             #     self.PRINT_ANSWER()


# # interpreter = Interpreter()
# # interpreter.execute(what_to_execute)

code = """
a = 10
b = 20
c = a + b
print(c)
"""


def compile_and_run_code(source):
    code_obj = compile(source, "<string>", "exec")
    vm = VirtualMachine()
    vm.run_code(code_obj)
    return vm.return_value

result = compile_and_run_code(code)
print("Result:", result)
