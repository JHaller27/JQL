using System;
using System.Text.RegularExpressions;

namespace Operations {
    class NotExpression : Expression {
        private static Regex OperationRegex = new Regex(@"^\-not$");

        public NotExpression(Operation[] args) : base(args) { }

        public override int RequiredArgs()
        {
            return 1;
        }

        public override Operation Clone(Operation[] args)
        {
            return new NotExpression(args);
        }

        public override bool CanParse(string token)
        {
            return OperationRegex.IsMatch(token);
        }

        internal override bool EvaluateAsBool()
        {
            return !Args[0].EvaluateAsBool();
        }
    }
}
