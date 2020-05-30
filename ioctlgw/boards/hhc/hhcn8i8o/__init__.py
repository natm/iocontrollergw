from ioctlgw.boards.baseinterface import BaseInterface


class HhcN8i8o(BaseInterface):

    def __init__(self, **kwargs):
        super(HhcN8i8o, self).__init__(num_digital_outputs=8, num_digital_inputs=8, **kwargs)
