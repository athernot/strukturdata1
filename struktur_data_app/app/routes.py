from flask import Blueprint, jsonify, request, render_template
from app import db
from app.models import Array, ArrayElement, LinkedList, ListNode, Queue, QueueElement, Stack, StackElement

main_bp = Blueprint('main', __name__)

# Home route
@main_bp.route('/')
def index():
    return render_template('index.html')

# Array routes
@main_bp.route('/arrays', methods=['GET'])
def get_arrays():
    arrays = Array.query.all()
    return jsonify([{
        'id': arr.id,
        'name': arr.name,
        'size': arr.size,
        'created_at': arr.created_at
    } for arr in arrays])

@main_bp.route('/arrays', methods=['POST'])
def create_array():
    data = request.json
    new_array = Array(name=data['name'], size=data['size'])
    db.session.add(new_array)
    db.session.commit()
    return jsonify({
        'id': new_array.id,
        'name': new_array.name,
        'size': new_array.size,
        'created_at': new_array.created_at
    })
@main_bp.route('/arrays/<int:array_id>', methods=['GET'])
def get_array(array_id):
    array = Array.query.get_or_404(array_id)
    elements = ArrayElement.query.filter_by(array_id=array_id).order_by(ArrayElement.position).all()
    return jsonify({
        'id': array.id,
        'name': array.name,
        'size': array.size,
        'elements': [{
            'position': elem.position,
            'value': elem.value
        } for elem in elements]
    })

@main_bp.route('/arrays/<int:array_id>/elements', methods=['POST'])
def set_array_element(array_id):
    array = Array.query.get_or_404(array_id)
    data = request.json
    
    if array.set_element(data['index'], data['value']):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Index out of bounds'}), 400

@main_bp.route('/arrays/<int:array_id>/search', methods=['GET'])
def search_array(array_id):
    array = Array.query.get_or_404(array_id)
    value = request.args.get('value', type=int)
    
    if value is None:
        return jsonify({'success': False, 'message': 'Value parameter required'}), 400
    
    positions = array.search(value)
    return jsonify({
        'success': True,
        'value': value,
        'positions': positions
    })

@main_bp.route('/arrays/<int:array_id>/elements/<int:index>', methods=['DELETE'])
def delete_array_element(array_id, index):
    array = Array.query.get_or_404(array_id)
    
    if array.delete_element(index):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Index out of bounds'}), 400

# Linked List routes
@main_bp.route('/linked-lists', methods=['GET'])
def get_linked_lists():
    lists = LinkedList.query.all()
    return jsonify([{
        'id': lst.id,
        'name': lst.name,
        'created_at': lst.created_at
    } for lst in lists])

@main_bp.route('/linked-lists', methods=['POST'])
def create_linked_list():
    data = request.json
    new_list = LinkedList(name=data['name'])
    db.session.add(new_list)
    db.session.commit()
    return jsonify({
        'id': new_list.id,
        'name': new_list.name,
        'created_at': new_list.created_at
    })

@main_bp.route('/linked-lists/<int:list_id>', methods=['GET'])
def get_linked_list(list_id):
    linked_list = LinkedList.query.get_or_404(list_id)
    nodes = linked_list.get_all_nodes()
    return jsonify({
        'id': linked_list.id,
        'name': linked_list.name,
        'nodes': [{
            'id': node.id,
            'value': node.value,
            'next_id': node.next_id
        } for node in nodes]
    })

@main_bp.route('/linked-lists/<int:list_id>/append', methods=['POST'])
def append_to_list(list_id):
    linked_list = LinkedList.query.get_or_404(list_id)
    data = request.json
    
    node = linked_list.append(data['value'])
    return jsonify({
        'success': True,
        'node_id': node.id,
        'value': node.value
    })

@main_bp.route('/linked-lists/<int:list_id>/prepend', methods=['POST'])
def prepend_to_list(list_id):
    linked_list = LinkedList.query.get_or_404(list_id)
    data = request.json
    
    node = linked_list.prepend(data['value'])
    return jsonify({
        'success': True,
        'node_id': node.id,
        'value': node.value
    })

@main_bp.route('/linked-lists/<int:list_id>/search', methods=['GET'])
def search_linked_list(list_id):
    linked_list = LinkedList.query.get_or_404(list_id)
    value = request.args.get('value', type=int)
    
    if value is None:
        return jsonify({'success': False, 'message': 'Value parameter required'}), 400
    
    node = linked_list.search(value)
    if node:
        return jsonify({
            'success': True,
            'node_id': node.id,
            'value': node.value,
            'next_id': node.next_id
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Value not found'
        })

@main_bp.route('/linked-lists/<int:list_id>/delete', methods=['DELETE'])
def delete_from_list(list_id):
    linked_list = LinkedList.query.get_or_404(list_id)
    data = request.json
    
    if linked_list.delete(data['value']):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Value not found'}), 404

# Queue routes
@main_bp.route('/queues', methods=['GET'])
def get_queues():
    queues = Queue.query.all()
    return jsonify([{
        'id': q.id,
        'name': q.name,
        'capacity': q.capacity,
        'size': q.size,
        'front': q.front,
        'rear': q.rear,
        'created_at': q.created_at
    } for q in queues])

@main_bp.route('/queues', methods=['POST'])
def create_queue():
    data = request.json
    new_queue = Queue(name=data['name'], capacity=data['capacity'])
    db.session.add(new_queue)
    db.session.commit()
    return jsonify({
        'id': new_queue.id,
        'name': new_queue.name,
        'capacity': new_queue.capacity,
        'size': new_queue.size,
        'front': new_queue.front,
        'rear': new_queue.rear,
        'created_at': new_queue.created_at
    })

@main_bp.route('/queues/<int:queue_id>', methods=['GET'])
def get_queue(queue_id):
    queue = Queue.query.get_or_404(queue_id)
    elements = queue.get_all_elements()
    return jsonify({
        'id': queue.id,
        'name': queue.name,
        'capacity': queue.capacity,
        'size': queue.size,
        'front': queue.front,
        'rear': queue.rear,
        'elements': [{
            'position': elem.position,
            'value': elem.value
        } for elem in elements]
    })

@main_bp.route('/queues/<int:queue_id>/enqueue', methods=['POST'])
def enqueue(queue_id):
    queue = Queue.query.get_or_404(queue_id)
    data = request.json
    
    if queue.enqueue(data['value']):
        return jsonify({
            'success': True,
            'size': queue.size,
            'front': queue.front,
            'rear': queue.rear
        })
    else:
        return jsonify({'success': False, 'message': 'Queue is full'}), 400

@main_bp.route('/queues/<int:queue_id>/dequeue', methods=['POST'])
def dequeue(queue_id):
    queue = Queue.query.get_or_404(queue_id)
    
    value = queue.dequeue()
    if value is not None:
        return jsonify({
            'success': True,
            'value': value,
            'size': queue.size,
            'front': queue.front,
            'rear': queue.rear
        })
    else:
        return jsonify({'success': False, 'message': 'Queue is empty'}), 400

# Stack routes
@main_bp.route('/stacks', methods=['GET'])
def get_stacks():
    stacks = Stack.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'capacity': s.capacity,
        'top': s.top,
        'created_at': s.created_at
    } for s in stacks])

@main_bp.route('/stacks', methods=['POST'])
def create_stack():
    data = request.json
    new_stack = Stack(name=data['name'], capacity=data['capacity'])
    db.session.add(new_stack)
    db.session.commit()
    return jsonify({
        'id': new_stack.id,
        'name': new_stack.name,
        'capacity': new_stack.capacity,
        'top': new_stack.top,
        'created_at': new_stack.created_at
    })

@main_bp.route('/stacks/<int:stack_id>', methods=['GET'])
def get_stack(stack_id):
    stack = Stack.query.get_or_404(stack_id)
    elements = stack.get_all_elements()
    return jsonify({
        'id': stack.id,
        'name': stack.name,
        'capacity': stack.capacity,
        'top': stack.top,
        'elements': [{
            'position': elem.position,
            'value': elem.value
        } for elem in elements]
    })

@main_bp.route('/stacks/<int:stack_id>/push', methods=['POST'])
def push(stack_id):
    stack = Stack.query.get_or_404(stack_id)
    data = request.json
    
    if stack.push(data['value']):
        return jsonify({
            'success': True,
            'top': stack.top
        })
    else:
        return jsonify({'success': False, 'message': 'Stack is full'}), 400

@main_bp.route('/stacks/<int:stack_id>/pop', methods=['POST'])
def pop(stack_id):
    stack = Stack.query.get_or_404(stack_id)
    
    value = stack.pop()
    if value is not None:
        return jsonify({
            'success': True,
            'value': value,
            'top': stack.top
        })
    else:
        return jsonify({'success': False, 'message': 'Stack is empty'}), 400

@main_bp.route('/stacks/<int:stack_id>/peek', methods=['GET'])
def peek(stack_id):
    stack = Stack.query.get_or_404(stack_id)
    
    value = stack.peek()
    if value is not None:
        return jsonify({
            'success': True,
            'value': value
        })
    else:
        return jsonify({'success': False, 'message': 'Stack is empty'}), 400