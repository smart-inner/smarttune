package tune

import (
	"fmt"
	"github.com/spf13/cobra"
)

func NewCmdRun() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "run [SESSION_NAME] [flags]",
		Short: "Start to tune the specified system",
		Long:  `Start to tune the specified system based on the registered session`,
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("Hello Tuning!")
		},
	}

	return cmd
}
