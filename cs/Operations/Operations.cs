using System;
using System.Collections.Generic;

namespace Operations
{
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

        internal virtual string EvaluateAsString()
        {
            throw new InvalidOperationException("Operation cannot be evaluated as a string");
        }

        internal virtual int EvaluateAsInt()
        {
            throw new InvalidOperationException("Operation cannot be evaluated as an integer");
        }

        internal virtual double EvaluateAsDouble()
        {
            throw new InvalidOperationException("Operation cannot be evaluated as a double");
        }

        internal virtual bool EvaluateAsBool()
        {
            throw new InvalidOperationException("Operation cannot be evaluated as a boolean");
        }

        internal virtual dynamic[] EvaluateAsArray()
        {
            throw new InvalidOperationException("Operation cannot be evaluated as an array");
        }

        internal virtual IDictionary<string, dynamic> EvaluateAsObject()
        {
            throw new InvalidOperationException("Operation cannot be evaluated as an object");
        }
    }

    abstract class Primitive : Operation
    {
        protected string Arg { get; }

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