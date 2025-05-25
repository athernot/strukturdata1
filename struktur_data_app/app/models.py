from datetime import datetime
from app import db

class Array(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    elements = db.relationship('ArrayElement', backref='array', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Array {self.name}>'
    
    def get_element(self, index):
        if 0 <= index < self.size:
            element = ArrayElement.query.filter_by(array_id=self.id, position=index).first()
            return element.value if element else None
        return None
    
    def set_element(self, index, value):
        if 0 <= index < self.size:
            element = ArrayElement.query.filter_by(array_id=self.id, position=index).first()
            if element:
                element.value = value
            else:
                element = ArrayElement(array_id=self.id, position=index, value=value)
                db.session.add(element)
            db.session.commit()
            return True
        return False
    
    def search(self, value):
        elements = ArrayElement.query.filter_by(array_id=self.id, value=value).all()
        return [element.position for element in elements]
    
    def delete_element(self, index):
        if 0 <= index < self.size:
            # Shift elements after deletion
            elements_to_shift = ArrayElement.query.filter(
                ArrayElement.array_id == self.id,
                ArrayElement.position > index
            ).all()
            
            # Delete the element at index
            ArrayElement.query.filter_by(array_id=self.id, position=index).delete()
            
            # Shift remaining elements
            for element in elements_to_shift:
                element.position -= 1
            
            db.session.commit()
            return True
        return False

class ArrayElement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    array_id = db.Column(db.Integer, db.ForeignKey('array.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    value = db.Column(db.Integer, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('array_id', 'position', name='uix_array_position'),
    )
    
    def __repr__(self):
        return f'<ArrayElement {self.position}: {self.value}>'

class LinkedList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    head_id = db.Column(db.Integer, db.ForeignKey('list_node.id'), nullable=True)
    nodes = db.relationship('ListNode', foreign_keys='ListNode.list_id', backref='linked_list', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<LinkedList {self.name}>'
    
    def append(self, value):
        new_node = ListNode(value=value, list_id=self.id)
        db.session.add(new_node)
        db.session.flush()  # To get the ID of the new node
        
        if self.head_id is None:
            self.head_id = new_node.id
        else:
            # Find the last node
            current_node = ListNode.query.get(self.head_id)
            while current_node.next_id is not None:
                current_node = ListNode.query.get(current_node.next_id)
            current_node.next_id = new_node.id
        
        db.session.commit()
        return new_node
    
    def prepend(self, value):
        new_node = ListNode(value=value, list_id=self.id)
        db.session.add(new_node)
        db.session.flush()  # To get the ID of the new node
        
        if self.head_id is not None:
            new_node.next_id = self.head_id
        
        self.head_id = new_node.id
        db.session.commit()
        return new_node
    
    def search(self, value):
        return ListNode.query.filter_by(list_id=self.id, value=value).first()
    
    def delete(self, value):
        if self.head_id is None:
            return False
        
        # If head node has the value
        head_node = ListNode.query.get(self.head_id)
        if head_node.value == value:
            self.head_id = head_node.next_id
            db.session.delete(head_node)
            db.session.commit()
            return True
        
        # Search for the node in the rest of the list
        current = head_node
        while current.next_id is not None:
            next_node = ListNode.query.get(current.next_id)
            if next_node.value == value:
                current.next_id = next_node.next_id
                db.session.delete(next_node)
                db.session.commit()
                return True
            current = next_node
        
        return False
    
    def get_all_nodes(self):
        nodes = []
        if self.head_id is not None:
            current = ListNode.query.get(self.head_id)
            while current is not None:
                nodes.append(current)
                if current.next_id is not None:
                    current = ListNode.query.get(current.next_id)
                else:
                    current = None
        return nodes

class ListNode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('linked_list.id'), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    next_id = db.Column(db.Integer, db.ForeignKey('list_node.id'), nullable=True)
    
    def __repr__(self):
        return f'<ListNode {self.value}>'

class Queue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    front = db.Column(db.Integer, default=0)
    rear = db.Column(db.Integer, default=-1)
    size = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    elements = db.relationship('QueueElement', backref='queue', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Queue {self.name}>'
    
    def is_empty(self):
        return self.size == 0
    
    def is_full(self):
        return self.size == self.capacity
    
    def enqueue(self, value):
        if self.is_full():
            return False
        
        self.rear = (self.rear + 1) % self.capacity
        self.size += 1
        
        # Check if element at position exists
        element = QueueElement.query.filter_by(queue_id=self.id, position=self.rear).first()
        if element:
            element.value = value
        else:
            element = QueueElement(queue_id=self.id, position=self.rear, value=value)
            db.session.add(element)
        
        db.session.commit()
        return True
    
    def dequeue(self):
        if self.is_empty():
            return None
        
        element = QueueElement.query.filter_by(queue_id=self.id, position=self.front).first()
        value = element.value if element else None
        
        self.front = (self.front + 1) % self.capacity
        self.size -= 1
        
        db.session.commit()
        return value
    
    def get_all_elements(self):
        if self.is_empty():
            return []
        
        elements = []
        count = self.size
        index = self.front
        
        while count > 0:
            element = QueueElement.query.filter_by(queue_id=self.id, position=index).first()
            if element:
                elements.append(element)
            index = (index + 1) % self.capacity
            count -= 1
        
        return elements

class QueueElement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    queue_id = db.Column(db.Integer, db.ForeignKey('queue.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    value = db.Column(db.Integer, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('queue_id', 'position', name='uix_queue_position'),
    )
    
    def __repr__(self):
        return f'<QueueElement {self.position}: {self.value}>'

class Stack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    top = db.Column(db.Integer, default=-1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    elements = db.relationship('StackElement', backref='stack', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Stack {self.name}>'
    
    def is_empty(self):
        return self.top == -1
    
    def is_full(self):
        return self.top == self.capacity - 1
    
    def push(self, value):
        if self.is_full():
            return False
        
        self.top += 1
        
        # Check if element at position exists
        element = StackElement.query.filter_by(stack_id=self.id, position=self.top).first()
        if element:
            element.value = value
        else:
            element = StackElement(stack_id=self.id, position=self.top, value=value)
            db.session.add(element)
        
        db.session.commit()
        return True
    
    def pop(self):
        if self.is_empty():
            return None
        
        element = StackElement.query.filter_by(stack_id=self.id, position=self.top).first()
        value = element.value if element else None
        
        self.top -= 1
        db.session.commit()
        return value
    
    def peek(self):
        if self.is_empty():
            return None
        
        element = StackElement.query.filter_by(stack_id=self.id, position=self.top).first()
        return element.value if element else None
    
    def get_all_elements(self):
        elements = StackElement.query.filter_by(stack_id=self.id).order_by(StackElement.position.desc()).all()
        return elements

class StackElement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stack_id = db.Column(db.Integer, db.ForeignKey('stack.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    value = db.Column(db.Integer, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('stack_id', 'position', name='uix_stack_position'),
    )
    
    def __repr__(self):
        return f'<StackElement {self.position}: {self.value}>'
