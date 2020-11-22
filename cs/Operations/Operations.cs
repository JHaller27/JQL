using System;
using System.Linq;
using System.Collections.Generic;

namespace Operations
{
    public class OperationParser
    {
        private static OperationParser Instance;

        private Operation[] PrototypePool { get; }

        private OperationParser()
        {
            PrototypePool = new Operation[]
            {
                // Must be in Order of Operations
            };
        }

        public static OperationParser GetInstance()
        {
            if (Instance == null)
            {
                Instance = new OperationParser();
            }

            return Instance;
        }

        public Operation Parse(Queue<string> tokens)
        {
            string token;
            while (tokens.TryDequeue(out token))
            {
                Operation prototype = PrototypePool.First(prototype => prototype.CanParse(token));

                if (prototype.IsPrimitive())
                {
                    return prototype.ClonePrimitive(token);
                }

                int numArgs = prototype.RequiredArgs();
                Operation[] args = new Operation[numArgs];
                for (int i = 0; i < numArgs; i++)
                {
                    args[i] = Parse(tokens);
                }

                return prototype.Clone(args);
            }

            throw new ArgumentException("Token Queue passed to Parse was empty - no tokens to parse.");
        }
    }

    public abstract class Operation
    {
        public bool Evaluate()
        {
            return EvaluateAsBool();
        }

        public abstract Operation Clone(Operation[] args);

        public abstract Operation ClonePrimitive(string arg);

        public abstract int RequiredArgs();

        public virtual bool IsPrimitive()
        {
            return false;
        }

        public virtual bool CanParse(string token)
        {
            return true;
        }

        protected virtual string EvaluateAsString()
        {
            throw new InvalidOperationException("Operation cannot be evaluated as a string");
        }

        protected virtual int EvaluateAsInt()
        {
            throw new InvalidOperationException("Operation cannot be evaluated as an integer");
        }

        protected virtual double EvaluateAsDouble()
        {
            throw new InvalidOperationException("Operation cannot be evaluated as a double");
        }

        protected virtual bool EvaluateAsBool()
        {
            throw new InvalidOperationException("Operation cannot be evaluated as a boolean");
        }

        // TODO Support EvaluateAsArray
        // TODO Support EvaluateAsObject
    }

    abstract class Primitive : Operation
    {
        private string Arg { get; set; }

        public Primitive(string arg)
        {
            Arg = arg;
        }

        public override int RequiredArgs()
        {
            return 1;
        }

        public override bool IsPrimitive()
        {
            return true;
        }

        public override Operation Clone(Operation[] args)
        {
            throw new InvalidOperationException("Primitive cannot be cloned as non-primitive");
        }
    }

    abstract class Expression : Operation
    {
        protected Operation[] Args { get; }

        public Expression(Operation[] args)
        {
            Args = args;
        }

        public override bool IsPrimitive()
        {
            return false;
        }

        public override Operation ClonePrimitive(string arg)
        {
            throw new InvalidOperationException("Expression cannot be cloned as primitive");
        }
    }
}