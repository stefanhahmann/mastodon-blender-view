package org.mastodon.blender;

import javax.swing.JOptionPane;
import org.jetbrains.annotations.NotNull;
import org.mastodon.blender.setup.BlenderSetupController;
import org.scijava.Context;
import org.scijava.prefs.PrefService;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.concurrent.CancellationException;

public class BlenderClient
{
	private final Context context;

	public BlenderClient( Context context )
	{
		this.context = context;
		Path blenderPath = null;//getBlenderPath( context );
		try {
			SetupBlender.startBlender( blenderPath );
		}
		catch ( Exception e ) {
			blenderPath = startSetupWithMessage( blenderPath );
			if(blenderPath == null)
				throw new CancellationException();
			try
			{
				SetupBlender.startBlender( blenderPath );
				setBlenderPath(blenderPath);
			}
			catch ( IOException ioException )
			{
				throw new RuntimeException( ioException );
			}
		}
	}

	private static Path startSetupWithMessage( Path blenderPath )
	{
		String message = appropriateMessage( blenderPath );
		int result = JOptionPane.showOptionDialog( null,
				message,
				"Problem Starting Mastodon",
				JOptionPane.OK_CANCEL_OPTION,
				JOptionPane.ERROR_MESSAGE,
				null,
				new Object[] { "Setup Blender", "Cancel" },
				null );
		if(result != JOptionPane.OK_OPTION )
			throw new CancellationException();
		return BlenderSetupController.showSetup( blenderPath );
	}

	@NotNull
	private static String appropriateMessage( Path blenderPath )
	{
		// not setup
		if( blenderPath == null)
			return "Blender has not yet been configured to be used from Mastodon.\n" +
					"Would you like to setup Blender.";

		// blender not found
		if( !Files.exists(blenderPath) )
			return "Blender wasn't found in the expected location:\n" +
					blenderPath.toAbsolutePath().toString() + "\n" +
					"Would you like to setup Blender to be used with Mastodon.";

		// plugin not installed
		// different plugin version
		// different error
		return "Blender didn't start as expected.\n" +
				"Maybe it has not been setup correctly, or something else changed.\n" +
				"Would you like to setup Blender to be used with Mastodon.";
	}

	private Path getBlenderPath( Context context )
	{
		PrefService prefs = context.service( PrefService.class );
		String string = prefs.get( BlenderClient.class, "BLENDER_BINARY_PATH" );
		return string == null ? null : Paths.get( string );
	}

	private void setBlenderPath( Path blenderPath )
	{
		PrefService prefs = context.service( PrefService.class );
		prefs.put( BlenderClient.class, "BLENDER_BINARY_PATH",
				blenderPath.toFile().getAbsolutePath() );
	}

	public void setTimepoint( int i )
	{
		throw new UnsupportedOperationException();
	}
}