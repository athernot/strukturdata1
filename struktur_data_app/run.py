from app import create_app, db
from app.models import Array, ArrayElement, LinkedList, ListNode, Queue, QueueElement, Stack, StackElement

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'Array': Array, 
        'ArrayElement': ArrayElement,
        'LinkedList': LinkedList,
        'ListNode': ListNode,
        'Queue': Queue,
        'QueueElement': QueueElement,
        'Stack': Stack,
        'StackElement': StackElement
    }

if __name__ == '__main__':
    app.run(debug=True)
