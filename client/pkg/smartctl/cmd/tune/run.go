package tune

import (
	"fmt"
	"github.com/smart-inner/smarttune/pkg/genericclioptions"
	"github.com/smart-inner/smarttune/util"
	"github.com/spf13/cobra"
)

type RunOptions struct {
	Backend string
	Url     string
	Tools   string

	genericclioptions.IOStreams
}

func NewRunOptions(streams genericclioptions.IOStreams) *RunOptions {
	return &RunOptions{
		IOStreams: streams,
	}
}

func NewCmdRun(streams genericclioptions.IOStreams) *cobra.Command {
	o := NewRunOptions(streams)
	cmd := &cobra.Command{
		Use:   "run SESSION_NAME --backend=backend [--url=url] [--tools=tools]",
		Short: "Start to tune the specified system",
		Long:  `Start to tune the specified system based on the created session`,
		Run: func(cmd *cobra.Command, args []string) {
			util.CheckErr(o.Run(args))
		},
	}

	addRunFlags(cmd, o)

	return cmd
}

func addRunFlags(cmd *cobra.Command, opt *RunOptions) {
	cmd.Flags().StringVar(&opt.Backend, "backend", "", "The backend url for smarttune, such as '127.0.0.1:5000'")
	cmd.Flags().StringVar(&opt.Url, "url", "", "The url for accessing target system")
	cmd.Flags().StringVar(&opt.Tools, "tools", "", "The tools for updating system's configuration")
}

func (o *RunOptions) Run(args []string) error {
	fmt.Println(args)
	fmt.Println(o.Backend)
	fmt.Println(o.Url)
	fmt.Println(o.Tools)
	return nil
}
