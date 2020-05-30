
class ComponentState(object):

    def __init__(self, component, num, status):
        self.component = component.strip().lower()
        self.num = int(num)
        self.status = status.strip().upper()

    def __repr__(self):
        return f"{self.component}_{self.num}_{self.status}"

    def __eq__(self, other):
        if self.component == other.component and self.num == other.num and self.status == other.status:
            return True
        return False
