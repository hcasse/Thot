@use box

# box Module

Allows to display text in boxes with different flavors. To use it:

```
@use box
```
And we can get:

<box info>
This is an info!
</box>

<box alert>
This is an alert!
</box>

<box download>
This is a download!
</box>

<box help>
This is help!
</box>

<box important>
This is important!
</box>

<box tip>
This is a tip!
</box>

<box todo>
This is a todo!
</box>

<box todo rounded>
This is a rounded todo!
</box>

<box content color=red text=blue rounded|Custom>
Custom!
</box>

And an example of code:
```
<box info>
This is an info!
</box>

<box alert>
This is an alert!
</box>

<box download>
This is a download!
</box>

<box help>
This is help!
</box>

<box important>
This is important!
</box>

<box tip>
This is a tip!
</box>

<box todo>
This is a todo!
</box>

<box todo rounded>
This is a rounded todo!
</box>

<box content color=red text=blue rounded|Custom>
Custom!
</box>
```

**This module only works with HTML output.** To customize further, the generated boxes supports specific classes to provide adapted CSS design:
* `box` is the main class,
* `box-`_type_ is the class provided by the type of box,
* `title` is the class of the title part,
* `body` is the class of the body part.

