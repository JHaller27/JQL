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
            // Try string
            try
            {
                return Args[0].EvaluateAsString().Equals(Args[1].EvaluateAsString());
            }
            catch (System.Exception) { }

            // Try int
            try
            {
                return Args[0].EvaluateAsInt().Equals(Args[1].EvaluateAsInt());
            }
            catch (System.Exception) { }

            // Try double
            try
            {
                return Args[0].EvaluateAsDouble().Equals(Args[1].EvaluateAsDouble());
            }
            catch (System.Exception) { }

            // Try bool
            try
            {
                return Args[0].EvaluateAsInt().Equals(Args[1].EvaluateAsBool());
            }
            catch (System.Exception) { }

            // Return false if types are different
            return false;
        }
    }
}
