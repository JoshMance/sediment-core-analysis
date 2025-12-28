using Avalonia;
using Avalonia.Controls;

namespace SedimentCoreApp.UI.Controls;

/// <summary>
/// A VS Code-style side panel with consistent chrome and arbitrary content.
/// </summary>
public class SidePanel : ContentControl
{
    public static readonly StyledProperty<string?> TitleProperty =
        AvaloniaProperty.Register<SidePanel, string?>(nameof(Title));

    public static readonly StyledProperty<bool> HasTitleProperty =
        AvaloniaProperty.Register<SidePanel, bool>(nameof(HasTitle), false);

    public string? Title
    {
        get => GetValue(TitleProperty);
        set => SetValue(TitleProperty, value);
    }

    public bool HasTitle
    {
        get => GetValue(HasTitleProperty);
        set => SetValue(HasTitleProperty, value);
    }
}
