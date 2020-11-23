namespace Operations
{
    class LiteralPrimitive : Primitive
    {
        public LiteralPrimitive(string arg) : base(arg) { }

        public override Operation ClonePrimitive(string arg)
        {
            return new LiteralPrimitive(arg);
        }

        public override bool CanParse(string token)
        {
            return true;
        }

        internal override string EvaluateAsString()
        {
            return Arg;
        }

        internal override int EvaluateAsInt()
        {
            return int.Parse(Arg);
        }

        internal override double EvaluateAsDouble()
        {
            return double.Parse(Arg);
        }

        internal override bool EvaluateAsBool()
        {
            return bool.Parse(Arg);
        }
    }
}
