all_regs = []

class Wire:
    def __init__(self, value=0):
        self.value = value

class RegInit:
    def __init__(self, value=0):
        self.cur_value = value
        self.next_value = value
        all_regs.append(self)

    def _pre_update(self):
        pass

    def _update(self):
        self.cur_value = self.next_value

class RegNext:
    def __init__(self, reg, init=0):
        self.cur_value = init
        self.next_value = init
        self.last_reg = reg

        all_regs.append(self)

    def _pre_update(self):
        self.next_value = self.last_reg.value

    def _update(self):
        self.cur_value = self.next_value

class RegEnable:
    def __init__(self, reg, enable):
        self.cur_value = 0
        self.next_value = 0
        self.last_reg = reg
        self.enable = enable

        all_regs.append(self)

    def _pre_update(self):
        self.next_value = self.last_reg.value if self.enable.value else self.cur_value

    def _update(self):
        self.cur_value = self.next_value


__RegInit_old_getattribute__ = RegInit.__getattribute__
def __RegInit_new_getattribute__(self, name):
    if name == "value":
        return self.cur_value
    else:
        return __RegInit_old_getattribute__(self, name)
RegInit.__getattribute__ = __RegInit_new_getattribute__


__RegInit_old_setattr__ = RegInit.__setattr__
def __RegInit_new_setattr__(self, name, value):
    if name == "value":
        self.next_value = value
    else:
        __RegInit_old_setattr__(self, name, value)
RegInit.__setattr__ = __RegInit_new_setattr__


__RegNext_old_getattribute__ = RegNext.__getattribute__
def __RegNext_new_getattribute__(self, name):
    if name == "value":
        return self.cur_value
    else:
        return __RegNext_old_getattribute__(self, name)
RegNext.__getattribute__ = __RegNext_new_getattribute__


__RegEnable_old_getattribute__ = RegEnable.__getattribute__
def __RegEnable_new_getattribute__(self, name):
    if name == "value":
        return self.cur_value
    else:
        return __RegEnable_old_getattribute__(self, name)


def update_regs():
    for reg in all_regs:
        reg._pre_update()
    for reg in all_regs:
        reg._update()
