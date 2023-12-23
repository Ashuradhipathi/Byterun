what_to_execute = { "instructions": [("LOAD_VALUE", 0),
    ("STORE_NAME", 0),
    ("LOAD_VALUE", 1),
    ("STORE_NAME", 1),
    ("LOAD_NAME",0),
    ("LOAD_NAME",1),
    ("ADD_TWO_VALUES", None),
    #("LOAD_VALUE", 2),
    #("ADD_TWO_VALUES", None),
    ("PRINT_ANSWER", None)],
"numbers":[1, 2],
"names":["a","b"]
}


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

    def run_frame(self):
        pass


class Function(object):
    """
    Create a realistic function object, defining the things the interpreter expects
    """
    __slots__ = [
        'func_code', 'func_name', 'func_defaults', 'func_globals',
        'func_locals', 'func_dict', 'func_closure', '__name__', '__dict__',
        '__doc__', '_vm', '_func'
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


class Interpreter:
    def __init__(self):
        self.stack = []
        self.environment = {}

    def STORE_NAME(self, name):
        val = self.stack.pop()
        self.environment[name] = val

    def LOAD_NAME(self, name):
        val = self.environment[name]
        self.stack.append(val)


    def parse_argument(self, instruction, argument, what_to_execute):
        """ Understand whta the argument to each instruction means"""
        numbers = ["LOAD_VALUE"]
        names = ["LOAD_NAME", "STORE_NAME"]

        if instruction in numbers:
            argument = what_to_execute["numbers"][argument]
        elif instruction in names:
            argument = what_to_execute["names"][argument]

        return argument
    
    def LOAD_VALUE(self, number):
        self.stack.append(number)

    def PRINT_ANSWER(self):
        answer = self.stack.pop()
        print(answer)

    def ADD_TWO_VALUES(self):
        #first_num = self.stack.pop()
        #second_num = self.stack.pop()
        #total = first_num + second_num
        #self.stack.append(total)
        self.stack.append(self.stack.pop() + self.stack.pop())


    def execute(self, what_to_execute):
        instructions = what_to_execute["instructions"]
        for each_step in instructions:
            instruction, argument = each_step
            argument = self.parse_argument(instruction=instruction, argument=argument, what_to_execute=what_to_execute)
            # if instruction == "LOAD_VALUE":
            #     self.LOAD_VALUE(argument)
            # elif instruction == "ADD_TWO_VALUES":
            #     self.ADD_TWO_VALUES()
            # elif instruction == "STORE_NAME":
            #     self.STORE_NAME(argument)
            # elif instruction == "LOAD_NAME":
            #     self.LOAD_NAME(argument)
            bytecode_method = getattr(self, instruction)
            if argument is None:
                bytecode_method()
            else:
                bytecode_method(argument)
            
            # elif instruction == "PRINT_ANSWER":
            #     self.PRINT_ANSWER()


# interpreter = Interpreter()
# interpreter.execute(what_to_execute)


        