from ioctlgw.boards.baseinterface import BaseInterface


class HiFlyingHF6508(BaseInterface):

    def __init__(self, **kwargs):
        super(HiFlyingHF6508, self).__init__(num_digital_outputs=8, num_digital_inputs=8, **kwargs)
