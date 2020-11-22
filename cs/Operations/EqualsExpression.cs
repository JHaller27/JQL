using System;
using System.Text.RegularExpressions;

namespace Operations {
    class EqualsExpression : Expression {
        private static Regex OperationRegex = new Regex(@"^\-eq$");

        public EqualsExpression(Operation[] args) : base(args) { }

        public override int RequiredArgs()
        {
            return 2;
        }

        public override Operation Clone(Operation[] args)
        {
            return new EqualsExpression(args);
        }

        public override bool CanParse(string token)
        {
            return OperationRegex.IsMatch(token);
        }

        internal override bool EvaluateAsBool()
        {
            return Args[0].EvaluateAsString().Equals(Args[1].EvaluateAsString());
        }
    }
}
