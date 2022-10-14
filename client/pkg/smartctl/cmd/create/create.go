package create

import (
	"fmt"
	"github.com/smart-inner/smarttune/pkg/genericclioptions"
	"github.com/smart-inner/smarttune/util"
	"github.com/spf13/cobra"
)

type CreateOptions struct {
	Backend string
	System  string
	Target  string

	genericclioptions.IOStreams
}

func NewCreateOptions(streams genericclioptions.IOStreams) *CreateOptions {
	return &CreateOptions{
		IOStreams: streams,
	}
}

func NewCmdCreate(streams genericclioptions.IOStreams) *cobra.Command {
	o := NewCreateOptions(streams)
	cmd := &cobra.Command{
		Use:   "create SESSION_NAME --backend=backend [--system=system] [--target=target]",
		Short: "Create session for the specified system",
		Long: `Create session, which include system type, system version, knobs catalog, metrics catalog
tuning algorithm and target objective.`,
		Run: func(cmd *cobra.Command, args []string) {
			util.CheckErr(o.Create(args))
		},
	}
	addCreateFlags(cmd, o)

	return cmd
}
func addCreateFlags(cmd *cobra.Command, opt *CreateOptions) {
	cmd.Flags().StringVar(&opt.Backend, "backend", "", "The backend url for smarttune, such as '127.0.0.1:5000'")
	cmd.Flags().StringVar(&opt.System, "system", "tidb@v6.1.0", "The system catalog for tuning")
	cmd.Flags().StringVar(&opt.Target, "target", "tidb.tidb_qps", "The target objective for tuning")
}

func (o *CreateOptions) Create(args []string) error {
	fmt.Println(args)
	fmt.Println(o.Backend)
	fmt.Println(o.System)
	fmt.Println(o.Target)
	return nil
}
