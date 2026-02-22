
class ExpressionEvaluator:
    """Evaluate mathematical expressions."""

    def __init__(self):
        """Initialize the evaluator with supported operators and their precedence."""
        self.operators = {'+': (1, lambda a, b: a + b), '-': (1, lambda a, b: a - b),
                          '*': (2, lambda a, b: a * b), '/': (2, lambda a, b: a / b), '^': (3,
                                                                                             lambda a, b: a ** b)}

    def evaluate(self, expression):
        """Evaluate a mathematical expression."""
        tokens = self._tokenize(expression)
        postfix = self._infix_to_postfix(tokens)
        return self._evaluate_postfix(postfix)

    def _tokenize(self, expression):
        """Tokenize expression into numbers and operators."""
        tokens = []
        current_number = ''
        for char in expression.replace(' ', ''):
            if char.isdigit() or char == '.':
                current_number += char
            else:
                if current_number:
                    tokens.append(float(current_number))
                    current_number = ''
                if char in self.operators or char in '()':
                    tokens.append(char)
        if current_number:
            tokens.append(float(current_number))
        return tokens

    def _infix_to_postfix(self, tokens):
        """Convert infix notation to postfix (RPN)."""
        output = []
        operator_stack = []
        for token in tokens:
            if isinstance(token, (int, float)):
                output.append(token)
            elif token == '(':
                operator_stack.append(token)
            elif token == ')':
                while operator_stack and operator_stack[-1] != '(':
                    output.append(operator_stack.pop())
                if operator_stack:
                    operator_stack.pop()  # Pop the '('
            elif token in self.operators:
                while operator_stack and operator_stack[-1] != '(' and operator_stack[-1] in self.operators and \
                        self.operators[operator_stack[-1]][0] >= self.operators[token][0]:
                    output.append(operator_stack.pop())
                operator_stack.append(token)
        while operator_stack:
            output.append(operator_stack.pop())
        return output

    def _evaluate_postfix(self, postfix):
        """Evaluate postfix expression."""
        stack = []
        for token in postfix:
            if isinstance(token, (int, float)):
                stack.append(token)
            elif token in self.operators:
                if len(stack) < 2:
                    return None  # Or raise an exception for invalid expression
                b = stack.pop()
                a = stack.pop()
                result = self.operators[token][1](a, b)
                stack.append(result)
        if len(stack) != 1:
            return None  # Or raise an exception for invalid expression
        return stack[0]


class ExpressionValidator:
    """Validates mathematical expressions."""

    @staticmethod
    def validate(expression):
        """Validate expression syntax."""
        if not expression or not expression.strip():
            return False, 'Empty expression'
        parentheses = 0
        for char in expression:
            if char == '(':
                parentheses += 1
            elif char == ')':
                parentheses -= 1
                if parentheses < 0:
                    return False, 'Unmatched closing parenthesis'
        if parentheses != 0:
            return False, 'Unmatched opening parenthesis'
        return True, 'Valid'


if __name__ == '__main__':
    evaluator = ExpressionEvaluator()
    validator = ExpressionValidator()
    expressions = ['2 + 3 * 4', '(2 + 3) * 4', '2 ^ 3 + 1']

    for expr in expressions:
        is_valid, message = validator.validate(expr)
        if is_valid:
            result = evaluator.evaluate(expr)
            print(f'{expr} = {result}')
        else:
            print(f'{expr}: {message}')
