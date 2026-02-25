using System;
using System.Threading;
using System.Threading.Tasks;

#nullable enable
public sealed class Counter
{
    private int _value;

    public int Increment() => Interlocked.Increment(ref _value);

    public int Value => Volatile.Read(ref _value);
}

public static class Perfect05_App
{
    public static int Main()
    {
        var counter = new Counter();
        var tasks = new Task[4];
        for (int i = 0; i < tasks.Length; i++)
        {
            tasks[i] = Task.Run(() =>
            {
                for (int j = 0; j < 10000; j++)
                    counter.Increment();
            });
        }

        Task.WaitAll(tasks);
        Console.WriteLine("Final value: " + counter.Value);
        return 0;
    }
}