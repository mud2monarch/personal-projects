package greetings

import "fmt"

// Hello returns a greeting for the named person.
func Hello(name string) string {
	message := fmt.Sprintf("hello %v. What's up?", name)
	return message
}
