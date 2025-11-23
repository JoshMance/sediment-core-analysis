using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace SedimentCoreApp.UI.ViewModels;

public enum ActiveTool
{
    None,
    File,
    Home,
    Analysis,
    Mapping,
    Export
}

public class MainWindowViewModel : INotifyPropertyChanged
{
    private ActiveTool _currentTool = ActiveTool.Home;

    public ActiveTool CurrentTool
    {
        get => _currentTool;
        set => SetField(ref _currentTool, value);
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }

    protected bool SetField<T>(ref T field, T value, [CallerMemberName] string? propertyName = null)
    {
        if (EqualityComparer<T>.Default.Equals(field, value)) return false;
        field = value;
        OnPropertyChanged(propertyName);
        return true;
    }
}
