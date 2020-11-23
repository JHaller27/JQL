using System;
using System.Text.RegularExpressions;

namespace Operations {
    class AndExpression : Expression {
        private static Regex OperationRegex = new Regex(@"^\-and$");

        public AndExpression(Operation[] args) : base(args) { }

        public override int RequiredArgs()
        {
            return 2;
        }

        public override Operation Clone(Operation[] args)
        {
            return new AndExpression(args);
        }

        public override bool CanParse(string token)
        {
            return OperationRegex.IsMatch(token);
        }

        internal override bool EvaluateAsBool()
        {
            return Args[0].EvaluateAsBool() && Args[1].EvaluateAsBool();
        }
    }
}
