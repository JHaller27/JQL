using System;
using System.Text.RegularExpressions;

namespace Operations {
    class OrExpression : Expression {
        private static Regex OperationRegex = new Regex(@"^\-or$");

        public OrExpression(Operation[] args) : base(args) { }

        public override int RequiredArgs()
        {
            return 2;
        }

        public override Operation Clone(Operation[] args)
        {
            return new OrExpression(args);
        }

        public override bool CanParse(string token)
        {
            return OperationRegex.IsMatch(token);
        }

        internal override bool EvaluateAsBool()
        {
            return Args[0].EvaluateAsBool() || Args[1].EvaluateAsBool();
        }
    }
}
