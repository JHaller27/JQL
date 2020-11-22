using System;
using System.Text.RegularExpressions;

namespace Operations {
    class NotEqualsExpression : Expression {
        private static Regex OperationRegex = new Regex(@"^\-ne$");

        private Operation OperationDelegate { get; set; }

        public NotEqualsExpression(Operation[] args) : base(args)
        {
            Operation equalsDelegate = new EqualsExpression(args);
            Operation[] notArgs = new Operation[] { equalsDelegate };
            OperationDelegate = new NotExpression(notArgs);
        }

        public override int RequiredArgs()
        {
            return 2;
        }

        public override Operation Clone(Operation[] args)
        {
            return new NotEqualsExpression(args);
        }

        public override bool CanParse(string token)
        {
            return OperationRegex.IsMatch(token);
        }

        internal override bool EvaluateAsBool()
        {
            return OperationDelegate.EvaluateAsBool();
        }
    }
}
