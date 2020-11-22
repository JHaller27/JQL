import sys

CLS_NAME=f"{sys.argv[1]}Expression"
PATH=f"./{CLS_NAME}.cs"

print(f"Creating {PATH} from template...")
with open(PATH, "w") as fout:
    template = f'''using System;
using System.Text.RegularExpressions;

namespace Operations {{
    class {CLS_NAME} : Expression {{
        private static Regex OperationRegex = new Regex(@"");

        public {CLS_NAME}(Operation[] args) : base(args) {{ }}

        public override int RequiredArgs()
        {{
            throw new NotImplementedException();
        }}

        public override Operation Clone(Operation[] args)
        {{
            return new {CLS_NAME}(args);
        }}

        public override bool CanParse(string token)
        {{
            return OperationRegex.IsMatch(token);
        }}

        internal override string EvaluateAsString()
        {{
            throw new InvalidOperationException("Operation cannot be evaluated as a string");
        }}

        internal override int EvaluateAsInt()
        {{
            throw new InvalidOperationException("Operation cannot be evaluated as an integer");
        }}

        internal override double EvaluateAsDouble()
        {{
            throw new InvalidOperationException("Operation cannot be evaluated as a double");
        }}

        internal override bool EvaluateAsBool()
        {{
            throw new InvalidOperationException("Operation cannot be evaluated as a boolean");
        }}
    }}
}}
'''
    fout.write(template)
