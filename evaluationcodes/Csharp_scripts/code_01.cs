using System;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;

#nullable enable
public static class Perfect01_LoadJson
{
    public static async Task<T?> LoadJsonAsync<T>(string path)
    {
        if (string.IsNullOrWhiteSpace(path))
            throw new ArgumentException("path is required", nameof(path));

        var file = new FileInfo(path);
        if (!file.Exists)
            throw new FileNotFoundException("JSON file not found", path);

        await using var stream = File.OpenRead(file.FullName);
        var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        var result = await JsonSerializer.DeserializeAsync<T>(stream, options).ConfigureAwait(false);
        return result;
    }

    public static async Task<int> Main(string[] args)
    {
        if (args.Length != 1)
        {
            Console.Error.WriteLine("Usage: Perfect01_LoadJson <path>");
            return 2;
        }

        try
        {
            var obj = await LoadJsonAsync<object>(args[0]).ConfigureAwait(false);
            Console.WriteLine(obj is null ? "null" : obj.ToString());
            return 0;
        }
        catch (FileNotFoundException ex)
        {
            Console.Error.WriteLine(ex.Message);
            return 3;
        }
        catch (JsonException ex)
        {
            Console.Error.WriteLine("Invalid JSON: " + ex.Message);
            return 4;
        }
    }
}