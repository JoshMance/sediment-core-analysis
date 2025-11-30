using System.Collections.Generic;
using System.Collections.ObjectModel;
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

public class MenuButton
{
    public string Label { get; set; } = string.Empty;
    public string IconPath { get; set; } = "/Assets/Icons/placeholder.svg";
}

public class ToolMenu
{
    public ActiveTool Tool { get; set; }
    public ObservableCollection<MenuButton> Buttons { get; set; } = new();
}

public class MainWindowViewModel : INotifyPropertyChanged
{
    private ActiveTool _currentTool = ActiveTool.Home;

    public ActiveTool CurrentTool
    {
        get => _currentTool;
        set => SetField(ref _currentTool, value);
    }

    public ObservableCollection<ToolMenu> ToolMenus { get; }

    public MainWindowViewModel()
    {
        ToolMenus = new ObservableCollection<ToolMenu>
        {
            new ToolMenu
            {
                Tool = ActiveTool.File,
                Buttons = new ObservableCollection<MenuButton>
                {
                    new MenuButton { Label = "New Project" },
                    new MenuButton { Label = "Open" },
                    new MenuButton { Label = "Save" },
                    new MenuButton { Label = "Close" }
                }
            },
            new ToolMenu
            {
                Tool = ActiveTool.Home,
                Buttons = new ObservableCollection<MenuButton>
                {
                    new MenuButton { Label = "Zoom In" },
                    new MenuButton { Label = "Zoom Out" },
                    new MenuButton { Label = "Fit to View" },
                    new MenuButton { Label = "Reset" }
                }
            },
            new ToolMenu
            {
                Tool = ActiveTool.Analysis,
                Buttons = new ObservableCollection<MenuButton>
                {
                    new MenuButton { Label = "Color Analysis" },
                    new MenuButton { Label = "Depth Markers" },
                    new MenuButton { Label = "Statistics" }
                }
            },
            new ToolMenu
            {
                Tool = ActiveTool.Mapping,
                Buttons = new ObservableCollection<MenuButton>
                {
                    new MenuButton { Label = "Add Marker" },
                    new MenuButton { Label = "Add Region" },
                    new MenuButton { Label = "Add Note" },
                    new MenuButton { Label = "Edit" }
                }
            },
            new ToolMenu
            {
                Tool = ActiveTool.Export,
                Buttons = new ObservableCollection<MenuButton>
                {
                    new MenuButton { Label = "Export CSV" },
                    new MenuButton { Label = "Export Image" },
                    new MenuButton { Label = "Export Report" }
                }
            }
        };
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
